"""Tests for revenue domain models and enums."""

from datetime import datetime, timezone
from decimal import Decimal
from uuid import uuid4
import pytest
from pydantic import ValidationError

from app.domain.revenue.enums import RevenueEventType
from app.domain.revenue.models import RevenueEvent


def test_revenue_event_creation_valid():
    """Test valid RevenueEvent creation with Decimal and string amount."""
    now = datetime.now(timezone.utc)
    merchant_id = uuid4()
    amount = Decimal("1500.75")

    event = RevenueEvent(
        merchant_id=merchant_id,
        event_type=RevenueEventType.PAYMENT_SUCCESS,
        source="razorpay_webhook",
        timestamp=now,
        amount=amount,
        currency="INR",
        metadata={"payment_id": "pay_123456"},
    )

    assert event.merchant_id == merchant_id
    assert event.event_type == RevenueEventType.PAYMENT_SUCCESS
    assert isinstance(event.amount, Decimal)
    assert event.amount == Decimal("1500.75")
    assert event.currency == "INR"


def test_revenue_event_string_amount_valid():
    """Test valid RevenueEvent creation using string amount representation."""
    now = datetime.now(timezone.utc)
    merchant_id = uuid4()

    event = RevenueEvent(
        merchant_id=merchant_id,
        event_type=RevenueEventType.PAYMENT_SUCCESS,
        source="razorpay_webhook",
        timestamp=now,
        amount="2500.00",
    )

    assert isinstance(event.amount, Decimal)
    assert event.amount == Decimal("2500.00")


def test_revenue_event_float_amount_rejection():
    """Test that python float amounts are explicitly rejected."""
    now = datetime.now(timezone.utc)
    merchant_id = uuid4()

    with pytest.raises(ValidationError, match="Float inputs are not allowed for monetary amounts"):
        RevenueEvent(
            merchant_id=merchant_id,
            event_type=RevenueEventType.PAYMENT_SUCCESS,
            source="razorpay_webhook",
            timestamp=now,
            amount=1500.75,  # float input
        )


def test_revenue_event_negative_amount_rejection():
    """Test that negative monetary amounts are rejected."""
    now = datetime.now(timezone.utc)
    merchant_id = uuid4()

    with pytest.raises(ValidationError, match="cannot be negative"):
        RevenueEvent(
            merchant_id=merchant_id,
            event_type=RevenueEventType.PAYMENT_FAILED,
            source="gateway_log",
            timestamp=now,
            amount=Decimal("-500.00"),
        )


def test_revenue_event_naive_datetime_rejection():
    """Test that naive datetimes are rejected."""
    merchant_id = uuid4()
    naive_dt = datetime.now()

    with pytest.raises(ValidationError):
        RevenueEvent(
            merchant_id=merchant_id,
            event_type=RevenueEventType.REFUND_INITIATED,
            source="gateway_log",
            timestamp=naive_dt,
            amount=Decimal("100.00"),
        )
