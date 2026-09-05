"""Tests for action domain models and enums."""

from datetime import datetime, timezone
from decimal import Decimal
from uuid import uuid4
import pytest
from pydantic import ValidationError

from app.domain.actions.enums import ActionStatus, ActionType, RiskLevel
from app.domain.actions.models import ActionPlan


def test_action_plan_creation_valid():
    """Test valid ActionPlan entity creation."""
    now = datetime.now(timezone.utc)
    incident_id = uuid4()

    plan = ActionPlan(
        incident_id=incident_id,
        action_type=ActionType.GATEWAY_REROUTE,
        target="razorpay_gateway_adapter",
        expected_recovery=Decimal("95000.00"),
        currency="INR",
        risk_level=RiskLevel.MEDIUM,
        confidence=Decimal("0.88"),
        approval_required=True,
        status=ActionStatus.PROPOSED,
        rationale="Reroute transaction traffic from degraded HDFC node to ICICI secondary pool",
        created_at=now,
    )

    assert plan.incident_id == incident_id
    assert plan.action_type == ActionType.GATEWAY_REROUTE
    assert plan.expected_recovery == Decimal("95000.00")
    assert plan.risk_level == RiskLevel.MEDIUM
    assert plan.approval_required is True


def test_action_plan_float_inputs_rejection():
    """Test that float inputs for expected_recovery and confidence are rejected."""
    now = datetime.now(timezone.utc)
    incident_id = uuid4()

    with pytest.raises(ValidationError, match="Float inputs are not allowed for monetary amounts"):
        ActionPlan(
            incident_id=incident_id,
            action_type=ActionType.RETRY_PAYMENT,
            target="payment_retry_queue",
            expected_recovery=95000.00,  # float input
            risk_level=RiskLevel.LOW,
            confidence=Decimal("0.80"),
            rationale="Test float expected_recovery rejection",
            created_at=now,
        )

    with pytest.raises(ValidationError, match="Float inputs are not allowed for confidence scores"):
        ActionPlan(
            incident_id=incident_id,
            action_type=ActionType.RETRY_PAYMENT,
            target="payment_retry_queue",
            expected_recovery=Decimal("95000.00"),
            risk_level=RiskLevel.LOW,
            confidence=0.80,  # float input
            rationale="Test float confidence rejection",
            created_at=now,
        )


def test_action_plan_negative_expected_recovery_rejection():
    """Test that negative expected recovery amounts are rejected."""
    now = datetime.now(timezone.utc)
    incident_id = uuid4()

    with pytest.raises(ValidationError):
        ActionPlan(
            incident_id=incident_id,
            action_type=ActionType.RETRY_PAYMENT,
            target="payment_retry_queue",
            expected_recovery=Decimal("-100.00"),
            risk_level=RiskLevel.LOW,
            confidence=Decimal("0.50"),
            rationale="Invalid negative recovery plan",
            created_at=now,
        )
