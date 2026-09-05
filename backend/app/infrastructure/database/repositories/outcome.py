"""SQLAlchemy implementation of OutcomeRepository."""

from typing import Optional
from uuid import UUID
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.ports.repositories import OutcomeRepository
from app.domain.outcomes.models import Outcome
from app.infrastructure.database.mappers import orm_to_outcome, outcome_to_orm
from app.infrastructure.database.models.outcome import OutcomeORM


class SQLAlchemyOutcomeRepository(OutcomeRepository):
    """SQLAlchemy Async implementation of OutcomeRepository port."""

    def __init__(self, session: AsyncSession):
        self._session = session

    async def save(self, outcome: Outcome) -> Outcome:
        """Persist or update an Outcome entity."""
        stmt = select(OutcomeORM).where(OutcomeORM.outcome_id == outcome.outcome_id)
        result = await self._session.execute(stmt)
        existing = result.scalar_one_or_none()

        if existing:
            existing.incident_id = outcome.incident_id
            existing.action_id = outcome.action_id
            existing.outcome_type = outcome.outcome_type.value
            existing.amount = outcome.amount
            existing.currency = outcome.currency
            existing.status = outcome.status.value
            existing.measured_at = outcome.measured_at
            existing.reference_data_json = dict(outcome.reference_data)
            orm_instance = existing
        else:
            orm_instance = outcome_to_orm(outcome)
            self._session.add(orm_instance)

        await self._session.flush()
        return orm_to_outcome(orm_instance)

    async def get_by_id(self, outcome_id: UUID) -> Optional[Outcome]:
        """Retrieve an Outcome by its unique identifier."""
        stmt = select(OutcomeORM).where(OutcomeORM.outcome_id == outcome_id)
        result = await self._session.execute(stmt)
        orm = result.scalar_one_or_none()
        return orm_to_outcome(orm) if orm else None

    async def get_by_action_id(self, action_id: UUID) -> Optional[Outcome]:
        """Retrieve an Outcome resulting from a specific ActionPlan."""
        stmt = select(OutcomeORM).where(OutcomeORM.action_id == action_id)
        result = await self._session.execute(stmt)
        orm = result.scalar_one_or_none()
        return orm_to_outcome(orm) if orm else None
