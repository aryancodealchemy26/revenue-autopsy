"""In-memory repository and UnitOfWork fakes for deterministic application unit testing."""

from typing import Any, Dict, List, Optional
from uuid import UUID

from app.application.ports.repositories import (
    ActionPlanRepository,
    EvidenceRepository,
    IncidentRepository,
    MerchantRepository,
    OutcomeRepository,
    RevenueEventRepository,
)
from app.application.ports.unit_of_work import UnitOfWork
from app.domain.actions.models import ActionPlan
from app.domain.incidents.models import Evidence, Incident
from app.domain.merchants.models import Merchant
from app.domain.outcomes.models import Outcome
from app.domain.revenue.models import RevenueEvent


class FakeMerchantRepository(MerchantRepository):
    """In-memory fake implementation of MerchantRepository."""

    def __init__(self):
        self._merchants: Dict[UUID, Merchant] = {}

    async def save(self, merchant: Merchant) -> Merchant:
        self._merchants[merchant.merchant_id] = merchant
        return merchant

    async def get_by_id(self, merchant_id: UUID) -> Optional[Merchant]:
        return self._merchants.get(merchant_id)


class FakeRevenueEventRepository(RevenueEventRepository):
    """In-memory fake implementation of RevenueEventRepository."""

    def __init__(self):
        self._events: Dict[UUID, RevenueEvent] = {}

    async def save(self, event: RevenueEvent) -> RevenueEvent:
        self._events[event.event_id] = event
        return event

    async def get_by_id(self, event_id: UUID) -> Optional[RevenueEvent]:
        return self._events.get(event_id)

    async def list_by_merchant(self, merchant_id: UUID, limit: int = 100) -> List[RevenueEvent]:
        events = [e for e in self._events.values() if e.merchant_id == merchant_id]
        events.sort(key=lambda x: x.timestamp, reverse=True)
        return events[:limit]


class FakeIncidentRepository(IncidentRepository):
    """In-memory fake implementation of IncidentRepository."""

    def __init__(self):
        self._incidents: Dict[UUID, Incident] = {}

    async def save(self, incident: Incident) -> Incident:
        self._incidents[incident.incident_id] = incident
        return incident

    async def get_by_id(self, incident_id: UUID) -> Optional[Incident]:
        return self._incidents.get(incident_id)

    async def list_by_merchant(self, merchant_id: UUID, limit: int = 50) -> List[Incident]:
        incidents = [inc for inc in self._incidents.values() if inc.merchant_id == merchant_id]
        incidents.sort(key=lambda x: x.detected_at, reverse=True)
        return incidents[:limit]


class FakeEvidenceRepository(EvidenceRepository):
    """In-memory fake implementation of EvidenceRepository."""

    def __init__(self):
        self._evidence: Dict[UUID, Evidence] = {}

    async def save(self, evidence: Evidence) -> Evidence:
        self._evidence[evidence.evidence_id] = evidence
        return evidence

    async def get_by_id(self, evidence_id: UUID) -> Optional[Evidence]:
        return self._evidence.get(evidence_id)

    async def list_by_incident(self, incident_id: UUID) -> List[Evidence]:
        ev_list = [e for e in self._evidence.values() if e.incident_id == incident_id]
        ev_list.sort(key=lambda x: x.observed_at, reverse=True)
        return ev_list


class FakeActionPlanRepository(ActionPlanRepository):
    """In-memory fake implementation of ActionPlanRepository."""

    def __init__(self):
        self._plans: Dict[UUID, ActionPlan] = {}

    async def save(self, plan: ActionPlan) -> ActionPlan:
        self._plans[plan.action_id] = plan
        return plan

    async def get_by_id(self, action_id: UUID) -> Optional[ActionPlan]:
        return self._plans.get(action_id)

    async def list_by_incident(self, incident_id: UUID) -> List[ActionPlan]:
        plans = [p for p in self._plans.values() if p.incident_id == incident_id]
        plans.sort(key=lambda x: x.created_at, reverse=True)
        return plans


class FakeOutcomeRepository(OutcomeRepository):
    """In-memory fake implementation of OutcomeRepository."""

    def __init__(self):
        self._outcomes: Dict[UUID, Outcome] = {}

    async def save(self, outcome: Outcome) -> Outcome:
        self._outcomes[outcome.outcome_id] = outcome
        return outcome

    async def get_by_id(self, outcome_id: UUID) -> Optional[Outcome]:
        return self._outcomes.get(outcome_id)

    async def get_by_action_id(self, action_id: UUID) -> Optional[Outcome]:
        for o in self._outcomes.values():
            if o.action_id == action_id:
                return o
        return None


class FakeUnitOfWork(UnitOfWork):
    """In-memory fake UnitOfWork managing fake repositories and transaction tracking."""

    def __init__(self):
        self.merchants = FakeMerchantRepository()
        self.revenue_events = FakeRevenueEventRepository()
        self.incidents = FakeIncidentRepository()
        self.evidence = FakeEvidenceRepository()
        self.action_plans = FakeActionPlanRepository()
        self.outcomes = FakeOutcomeRepository()
        self.committed = False
        self.rolled_back = False

    async def commit(self) -> None:
        self.committed = True

    async def rollback(self) -> None:
        self.rolled_back = True
