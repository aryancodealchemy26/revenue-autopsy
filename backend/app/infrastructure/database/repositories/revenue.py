"""SQLAlchemy implementation of RevenueEventRepository."""

from typing import List, Optional
from uuid import UUID
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.ports.repositories import RevenueEventRepository
from app.domain.revenue.models import RevenueEvent
from app.infrastructure.database.mappers import orm_to_revenue_event, revenue_event_to_orm
from app.infrastructure.database.models.revenue import RevenueEventORM


class SQLAlchemyRevenueEventRepository(RevenueEventRepository):
    """SQLAlchemy Async implementation of RevenueEventRepository port."""

    def __init__(self, session: AsyncSession):
        self._session = session

    async def save(self, event: RevenueEvent) -> RevenueEvent:
        """Persist a RevenueEvent entity."""
        stmt = select(RevenueEventORM).where(RevenueEventORM.event_id == event.event_id)
        result = await self._session.execute(stmt)
        existing = result.scalar_one_or_none()

        if existing:
            existing.merchant_id = event.merchant_id
            existing.event_type = event.event_type.value
            existing.source = event.source
            existing.timestamp = event.timestamp
            existing.amount = event.amount
            existing.currency = event.currency
            existing.metadata_json = dict(event.metadata)
            orm_instance = existing
        else:
            orm_instance = revenue_event_to_orm(event)
            self._session.add(orm_instance)

        await self._session.flush()
        return orm_to_revenue_event(orm_instance)

    async def get_by_id(self, event_id: UUID) -> Optional[RevenueEvent]:
        """Retrieve a RevenueEvent by its unique identifier."""
        stmt = select(RevenueEventORM).where(RevenueEventORM.event_id == event_id)
        result = await self._session.execute(stmt)
        orm = result.scalar_one_or_none()
        return orm_to_revenue_event(orm) if orm else None

    async def list_by_merchant(self, merchant_id: UUID, limit: int = 100) -> List[RevenueEvent]:
        """Retrieve telemetry events for a specific merchant."""
        stmt = (
            select(RevenueEventORM)
            .where(RevenueEventORM.merchant_id == merchant_id)
            .order_by(RevenueEventORM.timestamp.desc())
            .limit(limit)
        )
        result = await self._session.execute(stmt)
        return [orm_to_revenue_event(row) for row in result.scalars().all()]
