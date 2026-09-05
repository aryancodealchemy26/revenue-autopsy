"""API tests for /api/v1/incidents routes."""

from datetime import datetime, timezone
from decimal import Decimal
from uuid import uuid4
import pytest
from fastapi.testclient import TestClient

from app.ai.gateway import AIGateway
from app.ai.providers.fake_provider import FakeProvider
from app.api.dependencies.ai import get_ai_gateway
from app.api.dependencies.services import get_uow
from app.domain.incidents.enums import EvidenceType, IncidentSeverity, IncidentStatus, IncidentType
from app.domain.incidents.models import Evidence, Incident
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
async def test_list_incidents_tenant_isolated(client, fake_uow):
    """Verify listing incidents returns only those belonging to the authenticated merchant."""
    merchant_a = Merchant(merchant_id=uuid4(), name="Merchant A", currency="INR")
    merchant_b = Merchant(merchant_id=uuid4(), name="Merchant B", currency="INR")
    await fake_uow.merchants.save(merchant_a)
    await fake_uow.merchants.save(merchant_b)

    inc_a = Incident(
        incident_id=uuid4(),
        merchant_id=merchant_a.merchant_id,
        incident_type=IncidentType.PAYMENT_DROP_SPIKE,
        severity=IncidentSeverity.HIGH,
        status=IncidentStatus.DETECTED,
        detected_at=datetime.now(timezone.utc),
        revenue_at_risk=Decimal("45000.00"),
        currency="INR",
        confidence=Decimal("0.90"),
        description="Drop spike on Merchant A",
    )
    inc_b = Incident(
        incident_id=uuid4(),
        merchant_id=merchant_b.merchant_id,
        incident_type=IncidentType.AUTHORIZATION_FAILURE_SURGE,
        severity=IncidentSeverity.CRITICAL,
        status=IncidentStatus.DETECTED,
        detected_at=datetime.now(timezone.utc),
        revenue_at_risk=Decimal("125000.00"),
        currency="INR",
        confidence=Decimal("0.85"),
        description="Auth surge on Merchant B",
    )
    await fake_uow.incidents.save(inc_a)
    await fake_uow.incidents.save(inc_b)

    # Request as Merchant A
    response_a = client.get(
        "/api/v1/incidents",
        headers={"X-Merchant-ID": str(merchant_a.merchant_id)},
    )
    assert response_a.status_code == 200
    data_a = response_a.json()
    assert len(data_a) == 1
    assert data_a[0]["incident_id"] == str(inc_a.incident_id)

    # Request without merchant header
    response_missing = client.get("/api/v1/incidents")
    assert response_missing.status_code == 400


@pytest.mark.anyio
async def test_get_incident_cockpit_context(client, fake_uow):
    """Verify GET /incidents/{id} returns full aggregated context."""
    merchant = Merchant(merchant_id=uuid4(), name="Merchant Cockpit", currency="INR")
    await fake_uow.merchants.save(merchant)

    incident = Incident(
        incident_id=uuid4(),
        merchant_id=merchant.merchant_id,
        incident_type=IncidentType.PAYMENT_DROP_SPIKE,
        severity=IncidentSeverity.HIGH,
        status=IncidentStatus.DETECTED,
        detected_at=datetime.now(timezone.utc),
        revenue_at_risk=Decimal("45000.00"),
        currency="INR",
        confidence=Decimal("0.92"),
        description="HDFC gateway disruption",
    )
    await fake_uow.incidents.save(incident)

    evidence = Evidence(
        evidence_id=uuid4(),
        incident_id=incident.incident_id,
        evidence_type=EvidenceType.TELEMETRY_METRIC,
        source="gateway_stream",
        observed_at=datetime.now(timezone.utc),
        summary="504 gateway timeout",
        metrics_data={"error_rate": 0.45},
    )
    await fake_uow.evidence.save(evidence)

    response = client.get(
        f"/api/v1/incidents/{incident.incident_id}",
        headers={"X-Merchant-ID": str(merchant.merchant_id)},
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["incident"]["incident_id"] == str(incident.incident_id)
    assert len(payload["evidences"]) == 1
    assert payload["evidences"][0]["evidence_id"] == str(evidence.evidence_id)


@pytest.mark.anyio
async def test_get_incident_not_found_or_tenant_mismatch(client, fake_uow):
    """Verify foreign incident returns 404."""
    merchant_a = Merchant(merchant_id=uuid4(), name="Merchant A", currency="INR")
    merchant_b = Merchant(merchant_id=uuid4(), name="Merchant B", currency="INR")
    await fake_uow.merchants.save(merchant_a)
    await fake_uow.merchants.save(merchant_b)

    incident = Incident(
        incident_id=uuid4(),
        merchant_id=merchant_a.merchant_id,
        incident_type=IncidentType.PAYMENT_DROP_SPIKE,
        severity=IncidentSeverity.HIGH,
        status=IncidentStatus.DETECTED,
        detected_at=datetime.now(timezone.utc),
        revenue_at_risk=Decimal("45000.00"),
        currency="INR",
        confidence=Decimal("0.92"),
        description="Merchant A incident",
    )
    await fake_uow.incidents.save(incident)

    # Merchant B tries to access Merchant A's incident
    response = client.get(
        f"/api/v1/incidents/{incident.incident_id}",
        headers={"X-Merchant-ID": str(merchant_b.merchant_id)},
    )
    assert response.status_code == 404


@pytest.mark.anyio
async def test_investigate_incident_endpoint(client, fake_uow):
    """Verify POST /incidents/{id}/investigate triggers LangGraph workflow and returns structured results."""
    merchant = Merchant(merchant_id=uuid4(), name="Merchant AI", currency="INR")
    await fake_uow.merchants.save(merchant)

    incident = Incident(
        incident_id=uuid4(),
        merchant_id=merchant.merchant_id,
        incident_type=IncidentType.PAYMENT_DROP_SPIKE,
        severity=IncidentSeverity.HIGH,
        status=IncidentStatus.DETECTED,
        detected_at=datetime.now(timezone.utc),
        revenue_at_risk=Decimal("45000.00"),
        currency="INR",
        confidence=Decimal("0.92"),
        description="Payment drop spike on HDFC rail",
    )
    await fake_uow.incidents.save(incident)

    # Mock AI Gateway with FakeProvider
    provider = FakeProvider()
    call_count = 0

    async def dynamic_generate_json(*args, **kwargs):
        nonlocal call_count
        call_count += 1
        if call_count == 1:
            return (
                f'{{"incident_id": "{str(incident.incident_id)}", '
                f'"primary_cause": "HDFC gateway timeout", '
                f'"secondary_causes": [], '
                f'"confidence": 0.94, '
                f'"confidence_rationale": "High correlation with timeout errors", '
                f'"affected_cohorts": ["HDFC_NETBANKING"], '
                f'"evidence_keys_used": [], '
                f'"is_conclusive": true}}'
            )
        return (
            '{"action_type": "gateway_reroute", '
            '"target": "axis_secondary", '
            '"expected_recovery_ratio": 0.70, '
            '"risk_level": "low", '
            '"confidence": 0.90, '
            '"rationale": "Reroute traffic to secondary rail"}'
        )

    provider.generate_structured_json = dynamic_generate_json
    app.dependency_overrides[get_ai_gateway] = lambda: AIGateway(provider=provider, default_model="gpt-4o-mini")

    response = client.post(
        f"/api/v1/incidents/{incident.incident_id}/investigate",
        headers={"X-Merchant-ID": str(merchant.merchant_id)},
        json={},
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["investigation"]["primary_cause"] == "HDFC gateway timeout"
    assert payload["proposed_action"]["action_type"] == "gateway_reroute"
    assert payload["policy_decision"]["decision"] == "allow"
    assert payload["incident"]["status"] == "action_approved"
