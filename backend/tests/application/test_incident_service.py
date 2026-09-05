"""Tests for IncidentService application logic."""

from datetime import datetime, timezone
from decimal import Decimal
from uuid import uuid4
import pytest

from app.application.dtos.incidents import CreateIncidentDTO
from app.application.errors import (
    IncidentNotFoundError,
    InvalidStateTransitionError,
    MerchantNotFoundError,
)
from app.application.services.incident_service import IncidentService
from app.domain.incidents.enums import IncidentSeverity, IncidentStatus, IncidentType
from app.domain.merchants.models import Merchant
from tests.application.fakes import FakeUnitOfWork


@pytest.mark.anyio
async def test_create_incident_success():
    """Verify Incident creation commits entity when merchant exists."""
    uow = FakeUnitOfWork()
    service = IncidentService(uow)

    merchant = Merchant(merchant_id=uuid4(), name="Alpha Merchant", currency="INR")
    await uow.merchants.save(merchant)

    dto = CreateIncidentDTO(
        incident_id=uuid4(),
        merchant_id=merchant.merchant_id,
        incident_type=IncidentType.PAYMENT_DROP_SPIKE,
        severity=IncidentSeverity.HIGH,
        detected_at=datetime.now(timezone.utc),
        revenue_at_risk=Decimal("120000.0000"),
        currency="INR",
        confidence=Decimal("0.9000"),
        description="Drop spike detected",
    )

    incident = await service.create_incident(dto)

    assert incident.incident_id == dto.incident_id
    assert incident.merchant_id == merchant.merchant_id
    assert incident.revenue_at_risk == Decimal("120000.0000")
    assert incident.status == IncidentStatus.DETECTED
    assert uow.committed is True


@pytest.mark.anyio
async def test_create_incident_merchant_not_found():
    """Verify creating incident for missing merchant raises MerchantNotFoundError."""
    uow = FakeUnitOfWork()
    service = IncidentService(uow)

    dto = CreateIncidentDTO(
        merchant_id=uuid4(),
        incident_type=IncidentType.AUTHORIZATION_FAILURE_SURGE,
        severity=IncidentSeverity.CRITICAL,
        detected_at=datetime.now(timezone.utc),
        revenue_at_risk=Decimal("50000.0000"),
        currency="INR",
        confidence=Decimal("0.8500"),
        description="Missing merchant test",
    )

    with pytest.raises(MerchantNotFoundError):
        await service.create_incident(dto)


@pytest.mark.anyio
async def test_get_incident():
    """Verify incident retrieval and not found error handling."""
    uow = FakeUnitOfWork()
    service = IncidentService(uow)

    merchant = Merchant(merchant_id=uuid4(), name="Beta Merchant", currency="INR")
    await uow.merchants.save(merchant)

    dto = CreateIncidentDTO(
        merchant_id=merchant.merchant_id,
        incident_type=IncidentType.SETTLEMENT_DELAY,
        severity=IncidentSeverity.MEDIUM,
        detected_at=datetime.now(timezone.utc),
        revenue_at_risk=Decimal("30000.0000"),
        confidence=Decimal("0.8000"),
        description="Settlement delay",
    )
    created = await service.create_incident(dto)

    fetched = await service.get_incident(created.incident_id)
    assert fetched.incident_id == created.incident_id

    with pytest.raises(IncidentNotFoundError):
        await service.get_incident(uuid4())


@pytest.mark.anyio
async def test_update_incident_status_valid_and_invalid():
    """Verify status transition enforcement on incident updates."""
    uow = FakeUnitOfWork()
    service = IncidentService(uow)

    merchant = Merchant(merchant_id=uuid4(), name="Gamma Merchant", currency="INR")
    await uow.merchants.save(merchant)

    dto = CreateIncidentDTO(
        merchant_id=merchant.merchant_id,
        incident_type=IncidentType.PAYMENT_DROP_SPIKE,
        severity=IncidentSeverity.HIGH,
        detected_at=datetime.now(timezone.utc),
        revenue_at_risk=Decimal("20000.0000"),
        confidence=Decimal("0.8800"),
        description="State machine test",
    )
    created = await service.create_incident(dto)

    # Valid transition: DETECTED -> INVESTIGATING
    updated = await service.update_incident_status(created.incident_id, IncidentStatus.INVESTIGATING)
    assert updated.status == IncidentStatus.INVESTIGATING

    # Invalid transition: INVESTIGATING -> RESOLVED (cannot skip ACTION_PROPOSED/ACTION_APPROVED)
    with pytest.raises(InvalidStateTransitionError):
        await service.update_incident_status(created.incident_id, IncidentStatus.RESOLVED)


@pytest.mark.anyio
async def test_list_merchant_incidents():
    """Verify listing incidents for a merchant."""
    uow = FakeUnitOfWork()
    service = IncidentService(uow)

    merchant = Merchant(merchant_id=uuid4(), name="Delta Merchant", currency="INR")
    await uow.merchants.save(merchant)

    dto1 = CreateIncidentDTO(
        merchant_id=merchant.merchant_id,
        incident_type=IncidentType.DISPUTE_SPIKE,
        severity=IncidentSeverity.LOW,
        detected_at=datetime.now(timezone.utc),
        revenue_at_risk=Decimal("5000.0000"),
        confidence=Decimal("0.7000"),
        description="Dispute spike 1",
    )
    dto2 = CreateIncidentDTO(
        merchant_id=merchant.merchant_id,
        incident_type=IncidentType.WEBHOOK_LATENCY_SPIKE,
        severity=IncidentSeverity.MEDIUM,
        detected_at=datetime.now(timezone.utc),
        revenue_at_risk=Decimal("15000.0000"),
        confidence=Decimal("0.7500"),
        description="Webhook latency 2",
    )
    await service.create_incident(dto1)
    await service.create_incident(dto2)

    incidents = await service.list_merchant_incidents(merchant.merchant_id)
    assert len(incidents) == 2

    with pytest.raises(MerchantNotFoundError):
        await service.list_merchant_incidents(uuid4())
