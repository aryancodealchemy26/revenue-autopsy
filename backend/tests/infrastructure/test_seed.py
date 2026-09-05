"""Tests for Development & Demo Database Seeder."""

from decimal import Decimal
import pytest

from app.domain.incidents.enums import IncidentSeverity, IncidentStatus, IncidentType
from app.infrastructure.database.seed import (
    INCIDENT_CARD_AUTH_ID,
    INCIDENT_HDFC_ID,
    INCIDENT_SETTLEMENT_DELAY_ID,
    INCIDENT_WEBHOOK_LAG_ID,
    SANDBOX_MERCHANT_ID,
    seed_development_data,
)
from tests.application.fakes import FakeUnitOfWork


@pytest.mark.anyio
async def test_seed_development_data_creates_records():
    """Verify seed_development_data persists merchant, 4 incidents, and 7 evidence records."""
    uow = FakeUnitOfWork()

    result = await seed_development_data(uow)

    assert result["merchant"].merchant_id == SANDBOX_MERCHANT_ID
    assert len(result["incidents"]) == 4
    assert len(result["evidences"]) == 7
    assert uow.committed is True

    # Verify merchant persisted
    saved_merchant = await uow.merchants.get_by_id(SANDBOX_MERCHANT_ID)
    assert saved_merchant is not None
    assert saved_merchant.name == "Acme Digital Commerce Pvt Ltd"
    assert saved_merchant.currency == "INR"

    # Verify incidents persisted under merchant
    merchant_incidents = await uow.incidents.list_by_merchant(SANDBOX_MERCHANT_ID)
    assert len(merchant_incidents) == 4

    # Verify all incidents are DETECTED
    for inc in merchant_incidents:
        assert inc.status == IncidentStatus.DETECTED
        assert inc.merchant_id == SANDBOX_MERCHANT_ID
        assert inc.currency == "INR"


@pytest.mark.anyio
async def test_seed_development_data_is_idempotent():
    """Verify executing seed_development_data multiple times produces zero duplicates and no errors."""
    uow = FakeUnitOfWork()

    # First run
    await seed_development_data(uow)

    # Second run
    await seed_development_data(uow)

    # Assert merchant count is exactly 1
    saved_merchant = await uow.merchants.get_by_id(SANDBOX_MERCHANT_ID)
    assert saved_merchant is not None

    # Assert incident count is exactly 4
    merchant_incidents = await uow.incidents.list_by_merchant(SANDBOX_MERCHANT_ID)
    assert len(merchant_incidents) == 4

    # Assert evidence count for HDFC incident is exactly 3
    hdfc_evidence = await uow.evidence.list_by_incident(INCIDENT_HDFC_ID)
    assert len(hdfc_evidence) == 3

    # Assert evidence count for Card Auth incident is exactly 2
    card_evidence = await uow.evidence.list_by_incident(INCIDENT_CARD_AUTH_ID)
    assert len(card_evidence) == 2

    # Assert evidence count for Webhook Lag incident is exactly 1
    wh_evidence = await uow.evidence.list_by_incident(INCIDENT_WEBHOOK_LAG_ID)
    assert len(wh_evidence) == 1

    # Assert evidence count for Settlement Delay incident is exactly 1
    settle_evidence = await uow.evidence.list_by_incident(INCIDENT_SETTLEMENT_DELAY_ID)
    assert len(settle_evidence) == 1


@pytest.mark.anyio
async def test_seeded_scenarios_integrity():
    """Verify specific scenario attributes match domain and operational requirements."""
    uow = FakeUnitOfWork()
    await seed_development_data(uow)

    # 1. HDFC Netbanking Drop (Intended ALLOW)
    hdfc = await uow.incidents.get_by_id(INCIDENT_HDFC_ID)
    assert hdfc is not None
    assert hdfc.incident_type == IncidentType.PAYMENT_DROP_SPIKE
    assert hdfc.severity == IncidentSeverity.HIGH
    assert hdfc.revenue_at_risk == Decimal("45000.00")
    assert hdfc.confidence == Decimal("0.92")

    # 2. Card Auth Surge (Intended REQUIRE_APPROVAL)
    card = await uow.incidents.get_by_id(INCIDENT_CARD_AUTH_ID)
    assert card is not None
    assert card.incident_type == IncidentType.AUTHORIZATION_FAILURE_SURGE
    assert card.severity == IncidentSeverity.CRITICAL
    assert card.revenue_at_risk == Decimal("125000.00")
    assert card.confidence == Decimal("0.89")

    # 3. Webhook Latency Spike (Intended ALLOW)
    wh = await uow.incidents.get_by_id(INCIDENT_WEBHOOK_LAG_ID)
    assert wh is not None
    assert wh.incident_type == IncidentType.WEBHOOK_LATENCY_SPIKE
    assert wh.severity == IncidentSeverity.HIGH
    assert wh.revenue_at_risk == Decimal("18000.00")

    # 4. Settlement Delay (Intended ALLOW)
    settle = await uow.incidents.get_by_id(INCIDENT_SETTLEMENT_DELAY_ID)
    assert settle is not None
    assert settle.incident_type == IncidentType.SETTLEMENT_DELAY
    assert settle.severity == IncidentSeverity.MEDIUM
    assert settle.revenue_at_risk == Decimal("8500.00")
