"""SQLAlchemy implementation of ActionPlanRepository."""

from typing import List, Optional
from uuid import UUID
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.ports.repositories import ActionPlanRepository
from app.domain.actions.models import ActionPlan
from app.infrastructure.database.mappers import action_plan_to_orm, orm_to_action_plan
from app.infrastructure.database.models.action import ActionPlanORM


class SQLAlchemyActionPlanRepository(ActionPlanRepository):
    """SQLAlchemy Async implementation of ActionPlanRepository port."""

    def __init__(self, session: AsyncSession):
        self._session = session

    async def save(self, plan: ActionPlan) -> ActionPlan:
        """Persist or update an ActionPlan entity."""
        stmt = select(ActionPlanORM).where(ActionPlanORM.action_id == plan.action_id)
        result = await self._session.execute(stmt)
        existing = result.scalar_one_or_none()

        if existing:
            existing.incident_id = plan.incident_id
            existing.action_type = plan.action_type.value
            existing.target = plan.target
            existing.expected_recovery = plan.expected_recovery
            existing.currency = plan.currency
            existing.risk_level = plan.risk_level.value
            existing.confidence = plan.confidence
            existing.approval_required = plan.approval_required
            existing.status = plan.status.value
            existing.rationale = plan.rationale
            existing.created_at = plan.created_at
            orm_instance = existing
        else:
            orm_instance = action_plan_to_orm(plan)
            self._session.add(orm_instance)

        await self._session.flush()
        return orm_to_action_plan(orm_instance)

    async def get_by_id(self, action_id: UUID) -> Optional[ActionPlan]:
        """Retrieve an ActionPlan by its unique identifier."""
        stmt = select(ActionPlanORM).where(ActionPlanORM.action_id == action_id)
        result = await self._session.execute(stmt)
        orm = result.scalar_one_or_none()
        return orm_to_action_plan(orm) if orm else None

    async def list_by_incident(self, incident_id: UUID) -> List[ActionPlan]:
        """Retrieve action plans associated with an incident."""
        stmt = (
            select(ActionPlanORM)
            .where(ActionPlanORM.incident_id == incident_id)
            .order_by(ActionPlanORM.created_at.desc())
        )
        result = await self._session.execute(stmt)
        return [orm_to_action_plan(row) for row in result.scalars().all()]
