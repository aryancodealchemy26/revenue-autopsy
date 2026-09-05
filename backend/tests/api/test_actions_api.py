"""API tests for /api/v1/actions routes."""

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
async def test_get_action_plan_success(client, fake_uow):
    """Verify retrieving action plan within merchant boundary."""
    merchant = Merchant(merchant_id=uuid4(), name="Merchant Alpha", currency="INR")
    await fake_uow.merchants.save(merchant)

    incident = Incident(
        incident_id=uuid4(),
        merchant_id=merchant.merchant_id,
        incident_type=IncidentType.PAYMENT_DROP_SPIKE,
        severity=IncidentSeverity.HIGH,
        status=IncidentStatus.ACTION_PROPOSED,
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
        status=ActionStatus.APPROVED,
        rationale="Reroute traffic",
        created_at=datetime.now(timezone.utc),
    )
    await fake_uow.action_plans.save(action)

    response = client.get(
        f"/api/v1/actions/{action.action_id}",
        headers={"X-Merchant-ID": str(merchant.merchant_id)},
    )
    assert response.status_code == 200
    assert response.json()["action_id"] == str(action.action_id)


@pytest.mark.anyio
async def test_authorize_action_require_approval_succeeds(client, fake_uow):
    """Verify operator manual authorization of an action in REQUIRE_APPROVAL state."""
    merchant = Merchant(merchant_id=uuid4(), name="Merchant High Value", currency="INR")
    await fake_uow.merchants.save(merchant)

    incident = Incident(
        incident_id=uuid4(),
        merchant_id=merchant.merchant_id,
        incident_type=IncidentType.AUTHORIZATION_FAILURE_SURGE,
        severity=IncidentSeverity.CRITICAL,
        status=IncidentStatus.ACTION_PROPOSED,
        detected_at=datetime.now(timezone.utc),
        revenue_at_risk=Decimal("125000.00"),
        currency="INR",
        confidence=Decimal("0.89"),
        description="Card authorization surge",
    )
    await fake_uow.incidents.save(incident)

    action = ActionPlan(
        action_id=uuid4(),
        incident_id=incident.incident_id,
        action_type=ActionType.RETRY_PAYMENT,
        target="smart_retry_pool",
        expected_recovery=Decimal("85000.00"),
        currency="INR",
        risk_level=RiskLevel.MEDIUM,
        confidence=Decimal("0.85"),
        approval_required=True,
        status=ActionStatus.POLICY_CHECK_PENDING,
        rationale="Retry payment stream",
        created_at=datetime.now(timezone.utc),
    )
    await fake_uow.action_plans.save(action)

    response = client.post(
        f"/api/v1/actions/{action.action_id}/authorize",
        headers={"X-Merchant-ID": str(merchant.merchant_id)},
        json={"notes": "Authorized by risk team"},
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "approved"
    assert payload["approval_required"] is False


@pytest.mark.anyio
async def test_authorize_deny_rejected_action_fails(client, fake_uow):
    """Verify Policy DENIED/REJECTED actions can NEVER be authorized."""
    merchant = Merchant(merchant_id=uuid4(), name="Merchant Deny", currency="INR")
    await fake_uow.merchants.save(merchant)

    incident = Incident(
        incident_id=uuid4(),
        merchant_id=merchant.merchant_id,
        incident_type=IncidentType.PAYMENT_DROP_SPIKE,
        severity=IncidentSeverity.LOW,
        status=IncidentStatus.ACTION_PROPOSED,
        detected_at=datetime.now(timezone.utc),
        revenue_at_risk=Decimal("5000.00"),
        currency="INR",
        confidence=Decimal("0.80"),
        description="Low severity issue",
    )
    await fake_uow.incidents.save(incident)

    action = ActionPlan(
        action_id=uuid4(),
        incident_id=incident.incident_id,
        action_type=ActionType.GATEWAY_REROUTE,
        target="unknown_target",
        expected_recovery=Decimal("5000.00"),
        currency="INR",
        risk_level=RiskLevel.HIGH,
        confidence=Decimal("0.30"),
        approval_required=True,
        status=ActionStatus.REJECTED,
        rationale="Rejected due to low confidence",
        created_at=datetime.now(timezone.utc),
    )
    await fake_uow.action_plans.save(action)

    response = client.post(
        f"/api/v1/actions/{action.action_id}/authorize",
        headers={"X-Merchant-ID": str(merchant.merchant_id)},
        json={},
    )
    assert response.status_code == 403


@pytest.mark.anyio
async def test_execute_action_unapproved_fails(client, fake_uow):
    """Verify attempting to execute an unapproved action returns 400 ActionNotApprovedError."""
    merchant = Merchant(merchant_id=uuid4(), name="Merchant Exec", currency="INR")
    await fake_uow.merchants.save(merchant)

    incident = Incident(
        incident_id=uuid4(),
        merchant_id=merchant.merchant_id,
        incident_type=IncidentType.PAYMENT_DROP_SPIKE,
        severity=IncidentSeverity.HIGH,
        status=IncidentStatus.ACTION_PROPOSED,
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
        approval_required=True,
        status=ActionStatus.POLICY_CHECK_PENDING,
        rationale="Pending check",
        created_at=datetime.now(timezone.utc),
    )
    await fake_uow.action_plans.save(action)

    response = client.post(
        f"/api/v1/actions/{action.action_id}/execute",
        headers={"X-Merchant-ID": str(merchant.merchant_id)},
    )
    assert response.status_code == 400


@pytest.mark.anyio
async def test_execute_action_and_verify_outcome_flow(client, fake_uow):
    """Verify execution of approved action followed by deterministic verification."""
    merchant = Merchant(merchant_id=uuid4(), name="Merchant Full Flow", currency="INR")
    await fake_uow.merchants.save(merchant)

    incident = Incident(
        incident_id=uuid4(),
        merchant_id=merchant.merchant_id,
        incident_type=IncidentType.PAYMENT_DROP_SPIKE,
        severity=IncidentSeverity.HIGH,
        status=IncidentStatus.ACTION_APPROVED,
        detected_at=datetime.now(timezone.utc),
        revenue_at_risk=Decimal("45000.00"),
        currency="INR",
        confidence=Decimal("0.92"),
        description="HDFC Payment Drop Spike",
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
        status=ActionStatus.APPROVED,
        rationale="Reroute traffic to Axis rail",
        created_at=datetime.now(timezone.utc),
    )
    await fake_uow.action_plans.save(action)

    # 1. Execute
    exec_resp = client.post(
        f"/api/v1/actions/{action.action_id}/execute",
        headers={"X-Merchant-ID": str(merchant.merchant_id)},
    )
    assert exec_resp.status_code == 200
    exec_payload = exec_resp.json()
    assert exec_payload["status"] == "simulated"
    assert "idempotency_key" in exec_payload

    # 2. Duplicate execution fails with 409
    dup_resp = client.post(
        f"/api/v1/actions/{action.action_id}/execute",
        headers={"X-Merchant-ID": str(merchant.merchant_id)},
    )
    assert dup_resp.status_code == 409

    # 3. Verify Outcome
    verify_resp = client.post(
        f"/api/v1/actions/{action.action_id}/verify",
        headers={"X-Merchant-ID": str(merchant.merchant_id)},
    )
    assert verify_resp.status_code == 200
    outcome_payload = verify_resp.json()
    assert outcome_payload["outcome_type"] == "revenue_protected"
    assert outcome_payload["amount"] == "35000.00"
    assert outcome_payload["status"] == "verified"
