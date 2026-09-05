"""Action application service coordinating proposed intervention action plans."""

from typing import List
from uuid import UUID

from app.application.dtos.actions import CreateActionPlanDTO
from app.application.errors import ActionPlanNotFoundError, IncidentNotFoundError
from app.application.ports.unit_of_work import UnitOfWork
from app.application.state_machines import validate_action_transition
from app.domain.actions.enums import ActionStatus
from app.domain.actions.models import ActionPlan


class ActionService:
    """Application service for creating, retrieving, and managing action plan lifecycles."""

    def __init__(self, uow: UnitOfWork):
        self._uow = uow

    async def create_action_plan(self, incident_id: UUID, dto: CreateActionPlanDTO) -> ActionPlan:
        """Create and persist a proposed ActionPlan for an Incident."""
        async with self._uow:
            # 1. Verify incident exists
            incident = await self._uow.incidents.get_by_id(incident_id)
            if not incident:
                raise IncidentNotFoundError(incident_id)

            # 2. Construct domain ActionPlan
            plan = ActionPlan(
                action_id=dto.action_id,
                incident_id=incident_id,
                action_type=dto.action_type,
                target=dto.target,
                expected_recovery=dto.expected_recovery,
                currency=dto.currency,
                risk_level=dto.risk_level,
                confidence=dto.confidence,
                approval_required=dto.approval_required,
                status=dto.status,
                rationale=dto.rationale,
                created_at=dto.created_at,
            )

            # 3. Persist and commit
            saved = await self._uow.action_plans.save(plan)
            await self._uow.commit()
            return saved

    async def get_action_plan(self, action_id: UUID) -> ActionPlan:
        """Retrieve an ActionPlan by ID."""
        async with self._uow:
            plan = await self._uow.action_plans.get_by_id(action_id)
            if not plan:
                raise ActionPlanNotFoundError(action_id)
            return plan

    async def list_incident_action_plans(self, incident_id: UUID) -> List[ActionPlan]:
        """List all action plans associated with an Incident."""
        async with self._uow:
            incident = await self._uow.incidents.get_by_id(incident_id)
            if not incident:
                raise IncidentNotFoundError(incident_id)

            return await self._uow.action_plans.list_by_incident(incident_id)

    async def update_action_status(self, action_id: UUID, new_status: ActionStatus) -> ActionPlan:
        """Update an ActionPlan's lifecycle status enforcing transition rules."""
        async with self._uow:
            plan = await self._uow.action_plans.get_by_id(action_id)
            if not plan:
                raise ActionPlanNotFoundError(action_id)

            # Validate state transition
            validate_action_transition(plan.status, new_status)

            # Update status
            plan.status = new_status
            saved = await self._uow.action_plans.save(plan)
            await self._uow.commit()
            return saved
