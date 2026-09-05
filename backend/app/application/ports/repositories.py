"""Framework-agnostic repository interfaces (ports) for domain entities."""

from abc import ABC, abstractmethod
from typing import List, Optional
from uuid import UUID

from app.domain.actions.models import ActionPlan
from app.domain.incidents.models import Evidence, Incident
from app.domain.merchants.models import Merchant
from app.domain.outcomes.models import Outcome
from app.domain.revenue.models import RevenueEvent


class MerchantRepository(ABC):
    """Abstract repository port for Merchant entity persistence."""

    @abstractmethod
    async def save(self, merchant: Merchant) -> Merchant:
        """Persist or update a Merchant entity."""
        pass

    @abstractmethod
    async def get_by_id(self, merchant_id: UUID) -> Optional[Merchant]:
        """Retrieve a Merchant by its unique identifier."""
        pass


class RevenueEventRepository(ABC):
    """Abstract repository port for RevenueEvent persistence."""

    @abstractmethod
    async def save(self, event: RevenueEvent) -> RevenueEvent:
        """Persist a RevenueEvent entity."""
        pass

    @abstractmethod
    async def get_by_id(self, event_id: UUID) -> Optional[RevenueEvent]:
        """Retrieve a RevenueEvent by its unique identifier."""
        pass

    @abstractmethod
    async def list_by_merchant(self, merchant_id: UUID, limit: int = 100) -> List[RevenueEvent]:
        """Retrieve telemetry events for a specific merchant."""
        pass


class IncidentRepository(ABC):
    """Abstract repository port for Incident entity persistence."""

    @abstractmethod
    async def save(self, incident: Incident) -> Incident:
        """Persist or update an Incident entity."""
        pass

    @abstractmethod
    async def get_by_id(self, incident_id: UUID) -> Optional[Incident]:
        """Retrieve an Incident by its unique identifier."""
        pass

    @abstractmethod
    async def list_by_merchant(self, merchant_id: UUID, limit: int = 50) -> List[Incident]:
        """Retrieve revenue incidents associated with a merchant."""
        pass


class EvidenceRepository(ABC):
    """Abstract repository port for Evidence entity persistence."""

    @abstractmethod
    async def save(self, evidence: Evidence) -> Evidence:
        """Persist an Evidence item."""
        pass

    @abstractmethod
    async def get_by_id(self, evidence_id: UUID) -> Optional[Evidence]:
        """Retrieve an Evidence item by its unique identifier."""
        pass

    @abstractmethod
    async def list_by_incident(self, incident_id: UUID) -> List[Evidence]:
        """Retrieve evidence items associated with an incident."""
        pass


class ActionPlanRepository(ABC):
    """Abstract repository port for ActionPlan persistence."""

    @abstractmethod
    async def save(self, plan: ActionPlan) -> ActionPlan:
        """Persist or update an ActionPlan entity."""
        pass

    @abstractmethod
    async def get_by_id(self, action_id: UUID) -> Optional[ActionPlan]:
        """Retrieve an ActionPlan by its unique identifier."""
        pass

    @abstractmethod
    async def list_by_incident(self, incident_id: UUID) -> List[ActionPlan]:
        """Retrieve action plans associated with an incident."""
        pass


class OutcomeRepository(ABC):
    """Abstract repository port for Outcome persistence."""

    @abstractmethod
    async def save(self, outcome: Outcome) -> Outcome:
        """Persist an Outcome entity."""
        pass

    @abstractmethod
    async def get_by_id(self, outcome_id: UUID) -> Optional[Outcome]:
        """Retrieve an Outcome by its unique identifier."""
        pass

    @abstractmethod
    async def get_by_action_id(self, action_id: UUID) -> Optional[Outcome]:
        """Retrieve an Outcome resulting from a specific ActionPlan."""
        pass
