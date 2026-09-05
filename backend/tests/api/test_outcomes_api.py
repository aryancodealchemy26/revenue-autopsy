"""API tests for /api/v1/outcomes and provenance routes."""

from datetime import datetime, timezone
from decimal import Decimal
from uuid import uuid4
import pytest
from fastapi.testclient import TestClient

from app.api.dependencies.services import get_uow
from app.domain.actions.enums import ActionStatus, ActionType, RiskLevel
from app.domain.actions.models import ActionPlan
from app.domain.incidents.enums import IncidentSeverity, IncidentStatus, IncidentType
from app.domain.incidents.models import Incident
from app.domain.merchants.models import Merchant
from app.domain.outcomes.enums import OutcomeStatus, OutcomeType
from app.domain.outcomes.models import Outcome
from app.main import app
from tests.application.fakes import FakeUnitOfWork


@pytest.fixture
def fake_uow():
    return FakeUnitOfWork()


@pytest.fixture
def client(fake_uow):
    app.dependency_overrides[get_uow] = lambda: fake_uow
    yield TestClient(app)
    app.dependency_overrides.clear()


@pytest.mark.anyio
async def test_list_outcomes_merchant_isolated(client, fake_uow):
    """Verify GET /outcomes lists only outcomes belonging to the caller merchant."""
    merchant_a = Merchant(merchant_id=uuid4(), name="Merchant A", currency="INR")
    merchant_b = Merchant(merchant_id=uuid4(), name="Merchant B", currency="INR")
    await fake_uow.merchants.save(merchant_a)
    await fake_uow.merchants.save(merchant_b)

    inc_a = Incident(
        incident_id=uuid4(),
        merchant_id=merchant_a.merchant_id,
        incident_type=IncidentType.PAYMENT_DROP_SPIKE,
        severity=IncidentSeverity.HIGH,
        status=IncidentStatus.RESOLVED,
        detected_at=datetime.now(timezone.utc),
        revenue_at_risk=Decimal("45000.00"),
        currency="INR",
        confidence=Decimal("0.90"),
        description="Drop spike A",
    )
    await fake_uow.incidents.save(inc_a)

    act_a = ActionPlan(
        action_id=uuid4(),
        incident_id=inc_a.incident_id,
        action_type=ActionType.GATEWAY_REROUTE,
        target="axis_secondary",
        expected_recovery=Decimal("35000.00"),
        currency="INR",
        risk_level=RiskLevel.LOW,
        confidence=Decimal("0.90"),
        approval_required=False,
        status=ActionStatus.COMPLETED,
        rationale="Rerouted",
        created_at=datetime.now(timezone.utc),
    )
    await fake_uow.action_plans.save(act_a)

    out_a = Outcome(
        outcome_id=uuid4(),
        incident_id=inc_a.incident_id,
        action_id=act_a.action_id,
        outcome_type=OutcomeType.REVENUE_PROTECTED,
        amount=Decimal("35000.00"),
        currency="INR",
        status=OutcomeStatus.VERIFIED,
        measured_at=datetime.now(timezone.utc),
        reference_data={"recovery_rate": "0.7778"},
    )
    await fake_uow.outcomes.save(out_a)

    # Merchant A receives outcome
    resp_a = client.get(
        "/api/v1/outcomes",
        headers={"X-Merchant-ID": str(merchant_a.merchant_id)},
    )
    assert resp_a.status_code == 200
    data_a = resp_a.json()
    assert len(data_a) == 1
    assert data_a[0]["outcome_id"] == str(out_a.outcome_id)

    # Merchant B receives empty list
    resp_b = client.get(
        "/api/v1/outcomes",
        headers={"X-Merchant-ID": str(merchant_b.merchant_id)},
    )
    assert resp_b.status_code == 200
    data_b = resp_b.json()
    assert len(data_b) == 0


@pytest.mark.anyio
async def test_get_incident_provenance_stream(client, fake_uow):
    """Verify GET /incidents/{id}/provenance returns chronological audit events."""
    merchant = Merchant(merchant_id=uuid4(), name="Merchant Provenance", currency="INR")
    await fake_uow.merchants.save(merchant)

    incident = Incident(
        incident_id=uuid4(),
        merchant_id=merchant.merchant_id,
        incident_type=IncidentType.PAYMENT_DROP_SPIKE,
        severity=IncidentSeverity.HIGH,
        status=IncidentStatus.RESOLVED,
        detected_at=datetime.now(timezone.utc),
        revenue_at_risk=Decimal("45000.00"),
        currency="INR",
        confidence=Decimal("0.90"),
        description="Drop spike",
    )
    await fake_uow.incidents.save(incident)

    action = ActionPlan(
        action_id=uuid4(),
        incident_id=incident.incident_id,
        action_type=ActionType.GATEWAY_REROUTE,
        target="axis_secondary",
        expected_recovery=Decimal("35000.00"),
        currency="INR",
        risk_level=RiskLevel.LOW,
        confidence=Decimal("0.90"),
        approval_required=False,
        status=ActionStatus.COMPLETED,
        rationale="Rerouted",
        created_at=datetime.now(timezone.utc),
    )
    await fake_uow.action_plans.save(action)

    outcome = Outcome(
        outcome_id=uuid4(),
        incident_id=incident.incident_id,
        action_id=action.action_id,
        outcome_type=OutcomeType.REVENUE_PROTECTED,
        amount=Decimal("35000.00"),
        currency="INR",
        status=OutcomeStatus.VERIFIED,
        measured_at=datetime.now(timezone.utc),
        reference_data={},
    )
    await fake_uow.outcomes.save(outcome)

    resp = client.get(
        f"/api/v1/incidents/{incident.incident_id}/provenance",
        headers={"X-Merchant-ID": str(merchant.merchant_id)},
    )
    assert resp.status_code == 200
    events = resp.json()
    assert len(events) >= 2
    assert events[0]["step"] == "1. Incident Signal Detected"
