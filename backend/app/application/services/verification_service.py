"""Verification application service coordinating outcome recording and measurement retrieval."""

from typing import Optional
from uuid import UUID

from app.application.dtos.outcomes import RecordOutcomeDTO
from app.application.errors import (
    ActionPlanNotFoundError,
    ApplicationError,
    IncidentNotFoundError,
    OutcomeNotFoundError,
)
from app.application.ports.unit_of_work import UnitOfWork
from app.domain.outcomes.models import Outcome


class VerificationService:
    """Application service for recording and retrieving verified intervention outcomes."""

    def __init__(self, uow: UnitOfWork):
        self._uow = uow

    async def record_outcome(
        self, incident_id: UUID, action_id: UUID, dto: RecordOutcomeDTO
    ) -> Outcome:
        """Record and persist a measured outcome for an executed action."""
        async with self._uow:
            # 1. Verify Incident exists
            incident = await self._uow.incidents.get_by_id(incident_id)
            if not incident:
                raise IncidentNotFoundError(incident_id)

            # 2. Verify ActionPlan exists and matches Incident
            plan = await self._uow.action_plans.get_by_id(action_id)
            if not plan:
                raise ActionPlanNotFoundError(action_id)
            if plan.incident_id != incident_id:
                raise ApplicationError(
                    f"ActionPlan '{action_id}' does not belong to Incident '{incident_id}'."
                )

            # 3. Construct domain Outcome
            outcome = Outcome(
                outcome_id=dto.outcome_id,
                incident_id=incident_id,
                action_id=action_id,
                outcome_type=dto.outcome_type,
                amount=dto.amount,
                currency=dto.currency,
                status=dto.status,
                measured_at=dto.measured_at,
                reference_data=dto.reference_data,
            )

            # 4. Persist and commit
            saved = await self._uow.outcomes.save(outcome)
            await self._uow.commit()
            return saved

    async def get_outcome(self, outcome_id: UUID) -> Outcome:
        """Retrieve an Outcome by ID."""
        async with self._uow:
            outcome = await self._uow.outcomes.get_by_id(outcome_id)
            if not outcome:
                raise OutcomeNotFoundError(outcome_id)
            return outcome

    async def get_action_outcome(self, action_id: UUID) -> Optional[Outcome]:
        """Retrieve the Outcome associated with a specific ActionPlan."""
        async with self._uow:
            plan = await self._uow.action_plans.get_by_id(action_id)
            if not plan:
                raise ActionPlanNotFoundError(action_id)

            return await self._uow.outcomes.get_by_action_id(action_id)
