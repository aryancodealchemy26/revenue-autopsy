"""Tests for VerificationService application logic."""

from datetime import datetime, timezone
from decimal import Decimal
from uuid import uuid4
import pytest

from app.application.dtos.actions import CreateActionPlanDTO
from app.application.dtos.incidents import CreateIncidentDTO
from app.application.dtos.outcomes import RecordOutcomeDTO
from app.application.errors import (
    ActionPlanNotFoundError,
    ApplicationError,
    IncidentNotFoundError,
    OutcomeNotFoundError,
)
from app.application.services.action_service import ActionService
from app.application.services.incident_service import IncidentService
from app.application.services.verification_service import VerificationService
from app.domain.actions.enums import ActionType, RiskLevel
from app.domain.incidents.enums import IncidentSeverity, IncidentType
from app.domain.merchants.models import Merchant
from app.domain.outcomes.enums import OutcomeStatus, OutcomeType
from tests.application.fakes import FakeUnitOfWork


@pytest.mark.anyio
async def test_record_and_get_outcome():
    """Verify recording and querying a verified intervention Outcome."""
    uow = FakeUnitOfWork()
    incident_service = IncidentService(uow)
    action_service = ActionService(uow)
    verification_service = VerificationService(uow)

    merchant = Merchant(merchant_id=uuid4(), name="Verify Merchant", currency="INR")
    await uow.merchants.save(merchant)

    incident = await incident_service.create_incident(
        CreateIncidentDTO(
            merchant_id=merchant.merchant_id,
            incident_type=IncidentType.PAYMENT_DROP_SPIKE,
            severity=IncidentSeverity.CRITICAL,
            detected_at=datetime.now(timezone.utc),
            revenue_at_risk=Decimal("150000.0000"),
            confidence=Decimal("0.9000"),
            description="Drop spike",
        )
    )

    plan = await action_service.create_action_plan(
        incident.incident_id,
        CreateActionPlanDTO(
            action_type=ActionType.GATEWAY_REROUTE,
            target="secondary_gateway",
            expected_recovery=Decimal("120000.0000"),
            risk_level=RiskLevel.LOW,
            confidence=Decimal("0.8500"),
            rationale="Reroute traffic",
            created_at=datetime.now(timezone.utc),
        ),
    )

    outcome_dto = RecordOutcomeDTO(
        outcome_type=OutcomeType.REVENUE_RECOVERED,
        amount=Decimal("118500.0000"),
        currency="INR",
        status=OutcomeStatus.VERIFIED,
        measured_at=datetime.now(timezone.utc),
        reference_data={"recovered_tx_count": 142},
    )

    outcome = await verification_service.record_outcome(
        incident.incident_id, plan.action_id, outcome_dto
    )
    assert outcome.incident_id == incident.incident_id
    assert outcome.action_id == plan.action_id
    assert outcome.amount == Decimal("118500.0000")
    assert uow.committed is True

    fetched = await verification_service.get_outcome(outcome.outcome_id)
    assert fetched.outcome_id == outcome.outcome_id

    action_outcome = await verification_service.get_action_outcome(plan.action_id)
    assert action_outcome is not None
    assert action_outcome.outcome_id == outcome.outcome_id


@pytest.mark.anyio
async def test_record_outcome_mismatched_incident():
    """Verify recording outcome fails when ActionPlan does not belong to the Incident."""
    uow = FakeUnitOfWork()
    incident_service = IncidentService(uow)
    action_service = ActionService(uow)
    verification_service = VerificationService(uow)

    merchant = Merchant(merchant_id=uuid4(), name="Verify Merchant 2", currency="INR")
    await uow.merchants.save(merchant)

    inc1 = await incident_service.create_incident(
        CreateIncidentDTO(
            merchant_id=merchant.merchant_id,
            incident_type=IncidentType.PAYMENT_DROP_SPIKE,
            severity=IncidentSeverity.HIGH,
            detected_at=datetime.now(timezone.utc),
            revenue_at_risk=Decimal("50000.0000"),
            confidence=Decimal("0.8500"),
            description="Inc 1",
        )
    )

    inc2 = await incident_service.create_incident(
        CreateIncidentDTO(
            merchant_id=merchant.merchant_id,
            incident_type=IncidentType.AUTHORIZATION_FAILURE_SURGE,
            severity=IncidentSeverity.MEDIUM,
            detected_at=datetime.now(timezone.utc),
            revenue_at_risk=Decimal("30000.0000"),
            confidence=Decimal("0.8000"),
            description="Inc 2",
        )
    )

    plan = await action_service.create_action_plan(
        inc1.incident_id,
        CreateActionPlanDTO(
            action_type=ActionType.RETRY_PAYMENT,
            target="retry_service",
            expected_recovery=Decimal("20000.0000"),
            risk_level=RiskLevel.LOW,
            confidence=Decimal("0.8000"),
            rationale="Retry payments",
            created_at=datetime.now(timezone.utc),
        ),
    )

    outcome_dto = RecordOutcomeDTO(
        outcome_type=OutcomeType.REVENUE_RECOVERED,
        amount=Decimal("19000.0000"),
        measured_at=datetime.now(timezone.utc),
    )

    # Attempt to associate plan (which belongs to inc1) with inc2
    with pytest.raises(ApplicationError, match="does not belong to Incident"):
        await verification_service.record_outcome(inc2.incident_id, plan.action_id, outcome_dto)


@pytest.mark.anyio
async def test_verification_service_not_found_errors():
    """Verify error handling for missing entities in verification service."""
    uow = FakeUnitOfWork()
    verification_service = VerificationService(uow)

    with pytest.raises(IncidentNotFoundError):
        await verification_service.record_outcome(
            uuid4(),
            uuid4(),
            RecordOutcomeDTO(
                outcome_type=OutcomeType.NO_IMPACT,
                amount=Decimal("0.0000"),
                measured_at=datetime.now(timezone.utc),
            ),
        )

    with pytest.raises(OutcomeNotFoundError):
        await verification_service.get_outcome(uuid4())
