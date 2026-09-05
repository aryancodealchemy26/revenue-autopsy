"""SQLAlchemy concrete implementation of the UnitOfWork port."""

from typing import Any
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.ports.unit_of_work import UnitOfWork
from app.infrastructure.database.repositories.action import SQLAlchemyActionPlanRepository
from app.infrastructure.database.repositories.incident import (
    SQLAlchemyEvidenceRepository,
    SQLAlchemyIncidentRepository,
)
from app.infrastructure.database.repositories.merchant import SQLAlchemyMerchantRepository
from app.infrastructure.database.repositories.outcome import SQLAlchemyOutcomeRepository
from app.infrastructure.database.repositories.revenue import SQLAlchemyRevenueEventRepository


class SQLAlchemyUnitOfWork(UnitOfWork):
    """SQLAlchemy Async implementation of the UnitOfWork port."""

    def __init__(self, session: AsyncSession):
        self._session = session
        self.merchants = SQLAlchemyMerchantRepository(session)
        self.revenue_events = SQLAlchemyRevenueEventRepository(session)
        self.incidents = SQLAlchemyIncidentRepository(session)
        self.evidence = SQLAlchemyEvidenceRepository(session)
        self.action_plans = SQLAlchemyActionPlanRepository(session)
        self.outcomes = SQLAlchemyOutcomeRepository(session)

    async def __aenter__(self) -> "SQLAlchemyUnitOfWork":
        return self

    async def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        if exc_type is not None:
            await self.rollback()

    async def commit(self) -> None:
        """Commit pending transactions across all repositories."""
        await self._session.commit()

    async def rollback(self) -> None:
        """Roll back pending transactions."""
        await self._session.rollback()
