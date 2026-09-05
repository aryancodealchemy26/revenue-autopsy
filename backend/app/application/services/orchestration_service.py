"""Orchestration application service coordinating LangGraph intelligence workflows."""

import logging
from decimal import Decimal
from typing import Optional
from uuid import UUID

from app.agents.graph.state import IncidentInvestigationState, WorkflowStatus
from app.agents.graph.workflow import create_incident_investigation_graph
from app.ai.gateway import AIGateway
from app.application.errors import IncidentNotFoundError, MerchantNotFoundError
from app.application.ports.evidence_provider import EvidenceProvider
from app.application.ports.unit_of_work import UnitOfWork
from app.domain.incidents.enums import IncidentStatus

logger = logging.getLogger(__name__)


class IncidentOrchestrationService:
    """Coordinates incident investigation and recovery planning through LangGraph workflows."""

    def __init__(
        self,
        uow: UnitOfWork,
        gateway: AIGateway,
        evidence_provider: EvidenceProvider,
        model: Optional[str] = None,
    ):
        self._uow = uow
        self._gateway = gateway
        self._evidence_provider = evidence_provider
        self._model = model
        self._graph = create_incident_investigation_graph(
            gateway=self._gateway,
            evidence_provider=self._evidence_provider,
            model=self._model,
        )

    async def run_investigation_workflow(
        self,
        incident_id: UUID,
        baseline_hourly_rate: Optional[Decimal] = None,
        current_hourly_rate: Optional[Decimal] = None,
        duration_hours: Optional[Decimal] = None,
        correlation_id: Optional[str] = None,
    ) -> IncidentInvestigationState:
        """Execute end-to-end incident investigation and recovery planning workflow.

        Steps:
        1. Validate incident and merchant existence under trusted tenant context.
        2. Fetch diagnostic telemetry via EvidenceProvider.
        3. Execute compiled LangGraph state machine.
        4. Persist discovered evidence and proposed action plan within UoW transaction.
        5. Enforce state machine transitions on Incident and ActionPlan entities.
        """
        async with self._uow:
            # 1. Retrieve Incident and Merchant
            incident = await self._uow.incidents.get_by_id(incident_id)
            if not incident:
                raise IncidentNotFoundError(incident_id)

            merchant = await self._uow.merchants.get_by_id(incident.merchant_id)
            if not merchant:
                raise MerchantNotFoundError(incident.merchant_id)

            # 2. Update status to INVESTIGATING
            incident.status = IncidentStatus.INVESTIGATING
            await self._uow.incidents.save(incident)

            # 3. Retrieve deterministic evidence
            evidences = await self._evidence_provider.get_incident_evidence(
                merchant_id=incident.merchant_id,
                incident_id=incident.incident_id,
                incident_type=incident.incident_type,
                observed_after=incident.detected_at,
            )

            # Persist any evidence items not yet saved
            for ev in evidences:
                await self._uow.evidence.save(ev)

            # 4. Construct initial workflow state
            initial_state: IncidentInvestigationState = {
                "merchant_id": incident.merchant_id,
                "incident_id": incident.incident_id,
                "incident_type": incident.incident_type,
                "severity": incident.severity,
                "detected_at": incident.detected_at,
                "currency": incident.currency,
                "description": incident.description,
                "evidences": evidences,
                "baseline_hourly_rate": baseline_hourly_rate,
                "current_hourly_rate": current_hourly_rate,
                "duration_hours": duration_hours,
                "revenue_at_risk": incident.revenue_at_risk,
                "status": WorkflowStatus.INITIALIZED,
                "correlation_id": correlation_id,
            }

            # 5. Execute LangGraph workflow
            result_state: IncidentInvestigationState = await self._graph.ainvoke(initial_state)

            # 6. If ActionPlan proposed, persist and update incident status
            proposed_action = result_state.get("proposed_action")
            if proposed_action:
                await self._uow.action_plans.save(proposed_action)
                incident.status = IncidentStatus.ACTION_PROPOSED
                await self._uow.incidents.save(incident)

            # 7. Commit transaction
            await self._uow.commit()

            return result_state
