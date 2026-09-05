"""Tests for outcome domain models and enums."""

from datetime import datetime, timezone
from decimal import Decimal
from uuid import uuid4
import pytest
from pydantic import ValidationError

from app.domain.outcomes.enums import OutcomeStatus, OutcomeType
from app.domain.outcomes.models import Outcome


def test_outcome_creation_valid():
    """Test valid Outcome model creation."""
    now = datetime.now(timezone.utc)
    incident_id = uuid4()
    action_id = uuid4()

    outcome = Outcome(
        incident_id=incident_id,
        action_id=action_id,
        outcome_type=OutcomeType.REVENUE_RECOVERED,
        amount=Decimal("92500.00"),
        currency="INR",
        status=OutcomeStatus.VERIFIED,
        measured_at=now,
        reference_data={"recovered_transactions_count": 184},
    )

    assert outcome.incident_id == incident_id
    assert outcome.action_id == action_id
    assert outcome.outcome_type == OutcomeType.REVENUE_RECOVERED
    assert outcome.amount == Decimal("92500.00")
    assert outcome.status == OutcomeStatus.VERIFIED


def test_outcome_float_amount_rejection():
    """Test that float inputs for monetary amount are explicitly rejected."""
    now = datetime.now(timezone.utc)
    incident_id = uuid4()
    action_id = uuid4()

    with pytest.raises(ValidationError, match="Float inputs are not allowed for monetary amounts"):
        Outcome(
            incident_id=incident_id,
            action_id=action_id,
            outcome_type=OutcomeType.REVENUE_RECOVERED,
            amount=92500.00,  # float input
            measured_at=now,
        )


def test_outcome_serialization_deserialization():
    """Test JSON serialization and deserialization preserves Decimal and timezone."""
    now = datetime.now(timezone.utc)
    incident_id = uuid4()
    action_id = uuid4()

    outcome = Outcome(
        incident_id=incident_id,
        action_id=action_id,
        outcome_type=OutcomeType.REVENUE_PROTECTED,
        amount=Decimal("15000.50"),
        measured_at=now,
    )

    json_str = outcome.model_dump_json()
    reconstructed = Outcome.model_validate_json(json_str)

    assert reconstructed.outcome_id == outcome.outcome_id
    assert reconstructed.amount == Decimal("15000.50")
    assert isinstance(reconstructed.amount, Decimal)
    assert reconstructed.measured_at.tzinfo is not None
