"""Unit of Work interface port for managing transaction boundaries."""

from abc import ABC, abstractmethod
from typing import Any

from app.application.ports.repositories import (
    ActionPlanRepository,
    EvidenceRepository,
    IncidentRepository,
    MerchantRepository,
    OutcomeRepository,
    RevenueEventRepository,
)


class UnitOfWork(ABC):
    """Abstract Unit of Work port coordinating repositories and transaction boundaries."""

    merchants: MerchantRepository
    revenue_events: RevenueEventRepository
    incidents: IncidentRepository
    evidence: EvidenceRepository
    action_plans: ActionPlanRepository
    outcomes: OutcomeRepository

    async def __aenter__(self) -> "UnitOfWork":
        return self

    async def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        if exc_type is not None:
            await self.rollback()

    @abstractmethod
    async def commit(self) -> None:
        """Commit pending changes across all repositories."""
        pass

    @abstractmethod
    async def rollback(self) -> None:
        """Roll back pending changes across all repositories."""
        pass
