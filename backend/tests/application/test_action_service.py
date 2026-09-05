"""Tests for ActionService application logic."""

from datetime import datetime, timezone
from decimal import Decimal
from uuid import uuid4
import pytest

from app.application.dtos.actions import CreateActionPlanDTO
from app.application.dtos.incidents import CreateIncidentDTO
from app.application.errors import ActionPlanNotFoundError, IncidentNotFoundError, InvalidStateTransitionError
from app.application.services.action_service import ActionService
from app.application.services.incident_service import IncidentService
from app.domain.actions.enums import ActionStatus, ActionType, RiskLevel
from app.domain.incidents.enums import IncidentSeverity, IncidentType
from app.domain.merchants.models import Merchant
from tests.application.fakes import FakeUnitOfWork


@pytest.mark.anyio
async def test_create_and_get_action_plan():
    """Verify creating and retrieving an ActionPlan."""
    uow = FakeUnitOfWork()
    incident_service = IncidentService(uow)
    action_service = ActionService(uow)

    merchant = Merchant(merchant_id=uuid4(), name="Act Merchant", currency="INR")
    await uow.merchants.save(merchant)

    incident = await incident_service.create_incident(
        CreateIncidentDTO(
            merchant_id=merchant.merchant_id,
            incident_type=IncidentType.PAYMENT_DROP_SPIKE,
            severity=IncidentSeverity.CRITICAL,
            detected_at=datetime.now(timezone.utc),
            revenue_at_risk=Decimal("100000.0000"),
            confidence=Decimal("0.9000"),
            description="Drop spike",
        )
    )

    plan_dto = CreateActionPlanDTO(
        action_type=ActionType.GATEWAY_REROUTE,
        target="secondary_gateway_pool",
        expected_recovery=Decimal("85000.0000"),
        currency="INR",
        risk_level=RiskLevel.LOW,
        confidence=Decimal("0.8500"),
        approval_required=True,
        status=ActionStatus.PROPOSED,
        rationale="Switch gateway to secondary ICICI pool",
        created_at=datetime.now(timezone.utc),
    )

    plan = await action_service.create_action_plan(incident.incident_id, plan_dto)
    assert plan.incident_id == incident.incident_id
    assert plan.expected_recovery == Decimal("85000.0000")
    assert plan.status == ActionStatus.PROPOSED

    fetched = await action_service.get_action_plan(plan.action_id)
    assert fetched.action_id == plan.action_id

    plans = await action_service.list_incident_action_plans(incident.incident_id)
    assert len(plans) == 1


@pytest.mark.anyio
async def test_update_action_status_state_transitions():
    """Verify state transitions on action plans."""
    uow = FakeUnitOfWork()
    incident_service = IncidentService(uow)
    action_service = ActionService(uow)

    merchant = Merchant(merchant_id=uuid4(), name="Act Merchant 2", currency="INR")
    await uow.merchants.save(merchant)

    incident = await incident_service.create_incident(
        CreateIncidentDTO(
            merchant_id=merchant.merchant_id,
            incident_type=IncidentType.AUTHORIZATION_FAILURE_SURGE,
            severity=IncidentSeverity.HIGH,
            detected_at=datetime.now(timezone.utc),
            revenue_at_risk=Decimal("50000.0000"),
            confidence=Decimal("0.8500"),
            description="Auth surge",
        )
    )

    plan = await action_service.create_action_plan(
        incident.incident_id,
        CreateActionPlanDTO(
            action_type=ActionType.RETRY_PAYMENT,
            target="retry_service",
            expected_recovery=Decimal("30000.0000"),
            currency="INR",
            risk_level=RiskLevel.LOW,
            confidence=Decimal("0.8000"),
            rationale="Retry dropped transactions",
            created_at=datetime.now(timezone.utc),
        ),
    )

    # Valid transition: PROPOSED -> POLICY_CHECK_PENDING
    updated = await action_service.update_action_status(plan.action_id, ActionStatus.POLICY_CHECK_PENDING)
    assert updated.status == ActionStatus.POLICY_CHECK_PENDING

    # Valid transition: POLICY_CHECK_PENDING -> APPROVED
    updated2 = await action_service.update_action_status(plan.action_id, ActionStatus.APPROVED)
    assert updated2.status == ActionStatus.APPROVED

    # Invalid transition: APPROVED -> COMPLETED (cannot skip EXECUTING)
    with pytest.raises(InvalidStateTransitionError):
        await action_service.update_action_status(plan.action_id, ActionStatus.COMPLETED)


@pytest.mark.anyio
async def test_action_service_missing_entities():
    """Verify missing entity error handling in action service."""
    uow = FakeUnitOfWork()
    action_service = ActionService(uow)

    with pytest.raises(IncidentNotFoundError):
        await action_service.create_action_plan(
            uuid4(),
            CreateActionPlanDTO(
                action_type=ActionType.MERCHANT_ALERT,
                target="notification_service",
                expected_recovery=Decimal("0.0000"),
                risk_level=RiskLevel.LOW,
                confidence=Decimal("1.0000"),
                rationale="Send notification",
                created_at=datetime.now(timezone.utc),
            ),
        )

    with pytest.raises(ActionPlanNotFoundError):
        await action_service.get_action_plan(uuid4())
