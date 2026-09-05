"""Node execution functions and routers for the Revenue Incident LangGraph."""

import logging
from decimal import Decimal
from typing import Any, Dict, Optional

from app.agents.graph.state import IncidentInvestigationState, WorkflowStatus
from app.agents.investigator.agent import InvestigatorAgent
from app.agents.planner.agent import RecoveryPlannerAgent
from app.ai.errors import (
    AIGatewayError,
    AIProviderUnavailableError,
    AIRateLimitError,
    AIStructuredOutputValidationError,
    AITimeoutError,
    AITransientError,
)
from app.application.ports.evidence_provider import EvidenceProvider
from app.domain.revenue.calculations import calculate_revenue_at_risk

logger = logging.getLogger(__name__)


class IncidentWorkflowNodes:
    """Encapsulates node execution logic for the incident response workflow."""

    def __init__(
        self,
        investigator: InvestigatorAgent,
        planner: RecoveryPlannerAgent,
        evidence_provider: Optional[EvidenceProvider] = None,
    ):
        self._investigator = investigator
        self._planner = planner
        self._evidence_provider = evidence_provider

    async def investigator_node(self, state: IncidentInvestigationState) -> Dict[str, Any]:
        """Node 1: Evidence collection, financial quantification, and root-cause attribution."""
        merchant_id = state["merchant_id"]
        incident_id = state["incident_id"]
        incident_type = state["incident_type"]
        severity = state["severity"]
        description = state.get("description", "")
        currency = state.get("currency", "INR")
        correlation_id = state.get("correlation_id")

        # 1. Obtain deterministic evidence if not already populated
        evidences = state.get("evidences") or []
        if not evidences and self._evidence_provider:
            try:
                evidences = await self._evidence_provider.get_incident_evidence(
                    merchant_id=merchant_id,
                    incident_id=incident_id,
                    incident_type=incident_type,
                    observed_after=state.get("detected_at"),
                )
            except Exception as e:
                logger.error("Failed to retrieve evidence: %s", str(e), exc_info=e)
                return {
                    "status": WorkflowStatus.FAILED,
                    "error_message": f"Evidence collection error: {str(e)}",
                }

        # 2. Compute deterministic revenue at risk if hourly parameters provided
        revenue_at_risk = state.get("revenue_at_risk", Decimal("0.00"))
        baseline_rate = state.get("baseline_hourly_rate")
        current_rate = state.get("current_hourly_rate")
        duration_hours = state.get("duration_hours")

        if baseline_rate is not None and current_rate is not None and duration_hours is not None:
            revenue_at_risk = calculate_revenue_at_risk(
                baseline_hourly_rate=baseline_rate,
                current_hourly_rate=current_rate,
                duration_hours=duration_hours,
            )

        # 3. Execute Investigator Agent via AI Gateway
        try:
            result = await self._investigator.investigate(
                incident_id=str(incident_id),
                merchant_id=str(merchant_id),
                incident_type=incident_type.value if hasattr(incident_type, "value") else str(incident_type),
                severity=severity.value if hasattr(severity, "value") else str(severity),
                revenue_at_risk=revenue_at_risk,
                currency=currency,
                description=description,
                evidences=evidences,
                correlation_id=correlation_id,
            )
        except (AIRateLimitError, AITimeoutError, AIProviderUnavailableError, AITransientError) as e:
            logger.warning("AI provider transient error during investigation: %s", str(e))
            return {
                "evidences": evidences,
                "revenue_at_risk": revenue_at_risk,
                "status": WorkflowStatus.AI_UNAVAILABLE,
                "error_message": f"AI Gateway unavailable: {str(e)}",
            }
        except (AIStructuredOutputValidationError, AIGatewayError) as e:
            logger.error("AI Gateway structured output error: %s", str(e))
            return {
                "evidences": evidences,
                "revenue_at_risk": revenue_at_risk,
                "status": WorkflowStatus.FAILED,
                "error_message": f"Structured investigation error: {str(e)}",
            }
        except Exception as e:
            logger.error("Unexpected error in investigator node: %s", str(e), exc_info=e)
            return {
                "evidences": evidences,
                "revenue_at_risk": revenue_at_risk,
                "status": WorkflowStatus.FAILED,
                "error_message": str(e),
            }

        # 4. Check for inconclusive or low-confidence results
        if not result.is_conclusive:
            return {
                "evidences": evidences,
                "revenue_at_risk": revenue_at_risk,
                "investigation": result,
                "status": WorkflowStatus.INSUFFICIENT_EVIDENCE,
            }

        return {
            "evidences": evidences,
            "revenue_at_risk": revenue_at_risk,
            "investigation": result,
            "status": WorkflowStatus.INVESTIGATION_COMPLETE,
        }

    async def recovery_planner_node(self, state: IncidentInvestigationState) -> Dict[str, Any]:
        """Node 2: Formulate bounded ActionPlan based on conclusive root cause."""
        if state.get("status") != WorkflowStatus.INVESTIGATION_COMPLETE or not state.get("investigation"):
            return {}

        incident_id = state["incident_id"]
        incident_type = state["incident_type"]
        revenue_at_risk = state.get("revenue_at_risk", Decimal("0.00"))
        currency = state.get("currency", "INR")
        investigation = state["investigation"]
        correlation_id = state.get("correlation_id")

        try:
            plan = await self._planner.plan_recovery(
                incident_id=incident_id,
                incident_type=incident_type.value if hasattr(incident_type, "value") else str(incident_type),
                revenue_at_risk=revenue_at_risk,
                currency=currency,
                investigation=investigation,
                correlation_id=correlation_id,
            )
            return {
                "proposed_action": plan,
                "status": WorkflowStatus.COMPLETED,
            }
        except (AIRateLimitError, AITimeoutError, AIProviderUnavailableError, AITransientError) as e:
            logger.warning("AI provider transient error during recovery planning: %s", str(e))
            return {
                "status": WorkflowStatus.AI_UNAVAILABLE,
                "error_message": f"AI Gateway unavailable during planning: {str(e)}",
            }
        except (AIStructuredOutputValidationError, AIGatewayError) as e:
            logger.error("AI Gateway planning structured error: %s", str(e))
            return {
                "status": WorkflowStatus.FAILED,
                "error_message": f"Structured planning error: {str(e)}",
            }
        except Exception as e:
            logger.error("Unexpected error in planner node: %s", str(e), exc_info=e)
            return {
                "status": WorkflowStatus.FAILED,
                "error_message": str(e),
            }


def route_after_investigation(state: IncidentInvestigationState) -> str:
    """Conditional router determining whether to proceed to recovery planner or terminate."""
    status = state.get("status")
    if status == WorkflowStatus.INVESTIGATION_COMPLETE:
        return "recovery_planner"
    return "end"
