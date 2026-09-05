"""Recovery Planner Agent proposing bounded mitigation ActionPlans via AIGateway."""

from datetime import datetime, timezone
from decimal import Decimal
from typing import Optional
from uuid import UUID, uuid4

from app.agents.investigator.schemas import InvestigationResult
from app.agents.planner.schemas import RecoveryPlanProposal
from app.ai.gateway import AIGateway
from app.ai.schemas.messages import ChatMessage, MessageRole
from app.domain.actions.enums import ActionStatus, ActionType
from app.domain.actions.models import ActionPlan
from app.domain.revenue.calculations import calculate_expected_recovery


PLANNER_SYSTEM_PROMPT = """You are the Revenue Recovery Planner Agent for Revenue Autopsy.
Your purpose is to receive an established root-cause investigation result and propose a bounded, non-destructive recovery or protection action plan.

STRICT OPERATIONAL RULES:
1. You must select ONLY from approved domain ActionTypes:
   - gateway_reroute (e.g. reroute degraded bank routes to secondary gateways)
   - retry_payment (e.g. scheduled smart retry for transient authorization/gateway drops)
   - merchant_alert (e.g. alert merchant ops for webhook/endpoint misconfiguration)
   - webhook_resync (e.g. replay missing webhook event notifications)
   - rate_limit_adjustment (e.g. throttle or adjust burst limits on payment APIs)
2. You do NOT execute any action or call Razorpay write APIs.
3. You propose an `expected_recovery_ratio` (between 0.0 and 1.0) representing what fraction of the revenue at risk is realistically recoverable.
4. Assess the risk level honestly (LOW, MEDIUM, HIGH).
5. Provide a clear technical rationale for why this action mitigates the identified root cause.
"""


class RecoveryPlannerAgent:
    """Agent responsible for formulating candidate mitigation ActionPlans."""

    def __init__(self, gateway: AIGateway, model: Optional[str] = None):
        self._gateway = gateway
        self._model = model

    def _build_prompt_content(
        self,
        incident_id: str,
        incident_type: str,
        revenue_at_risk: str,
        currency: str,
        investigation: InvestigationResult,
    ) -> str:
        cohorts_str = ", ".join(investigation.affected_cohorts) if investigation.affected_cohorts else "Global/All"
        secondaries_str = "; ".join(investigation.secondary_causes) if investigation.secondary_causes else "None"

        return (
            f"=== INVESTIGATION REPORT ===\n"
            f"Incident ID: {incident_id}\n"
            f"Incident Type: {incident_type}\n"
            f"Deterministic Revenue at Risk: {currency} {revenue_at_risk}\n"
            f"Primary Cause: {investigation.primary_cause}\n"
            f"Secondary Causes: {secondaries_str}\n"
            f"Investigation Confidence: {investigation.confidence}\n"
            f"Affected Cohorts: {cohorts_str}\n"
            f"Confidence Rationale: {investigation.confidence_rationale}\n\n"
            f"Propose the optimal bounded recovery action plan."
        )

    async def plan_recovery(
        self,
        incident_id: UUID,
        incident_type: str,
        revenue_at_risk: Decimal,
        currency: str,
        investigation: InvestigationResult,
        correlation_id: Optional[str] = None,
    ) -> ActionPlan:
        """Formulate a structured recovery plan and convert it into a domain ActionPlan."""
        prompt_content = self._build_prompt_content(
            incident_id=str(incident_id),
            incident_type=incident_type,
            revenue_at_risk=str(revenue_at_risk),
            currency=currency,
            investigation=investigation,
        )

        messages = [
            ChatMessage(role=MessageRole.system, content=PLANNER_SYSTEM_PROMPT),
            ChatMessage(role=MessageRole.user, content=prompt_content),
        ]

        proposal = await self._gateway.generate_structured(
            messages=messages,
            response_model=RecoveryPlanProposal,
            model=self._model,
            correlation_id=correlation_id,
        )

        # Deterministically calculate expected recovery amount in domain
        expected_recovery_amount = calculate_expected_recovery(
            revenue_at_risk=revenue_at_risk,
            recovery_ratio=proposal.expected_recovery_ratio,
        )

        # Construct and return validated domain ActionPlan
        return ActionPlan(
            action_id=uuid4(),
            incident_id=incident_id,
            action_type=proposal.action_type,
            target=proposal.target,
            expected_recovery=expected_recovery_amount,
            currency=currency,
            risk_level=proposal.risk_level,
            confidence=proposal.confidence,
            approval_required=True,
            status=ActionStatus.PROPOSED,
            rationale=proposal.rationale,
            created_at=datetime.now(timezone.utc),
        )
