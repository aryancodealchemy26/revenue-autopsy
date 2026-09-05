"""Tests for shared domain validators and rules."""

from datetime import datetime, timezone
from decimal import Decimal
import pytest

from app.domain.shared import (
    validate_confidence_score,
    validate_currency_code,
    validate_non_negative_decimal,
    validate_timezone_aware,
)


def test_validate_timezone_aware():
    """Verify timezone-aware datetimes pass and naive datetimes are rejected."""
    aware_dt = datetime.now(timezone.utc)
    assert validate_timezone_aware(aware_dt) == aware_dt

    naive_dt = datetime.now()
    with pytest.raises(ValueError, match="timezone-aware"):
        validate_timezone_aware(naive_dt)


def test_validate_non_negative_decimal_valid():
    """Verify Decimal objects and string representations pass."""
    dec = Decimal("100.50")
    assert validate_non_negative_decimal(dec) == dec

    str_dec = "100.50"
    assert validate_non_negative_decimal(str_dec) == Decimal("100.50")

    zero_dec = Decimal("0.00")
    assert validate_non_negative_decimal(zero_dec) == zero_dec


def test_validate_non_negative_decimal_rejects_floats():
    """Verify python float inputs are explicitly rejected."""
    with pytest.raises(ValueError, match="Float inputs are not allowed for monetary amounts"):
        validate_non_negative_decimal(100.50)

    with pytest.raises(ValueError, match="Float inputs are not allowed for monetary amounts"):
        validate_non_negative_decimal(0.0)


def test_validate_non_negative_decimal_rejects_negative():
    """Verify negative Decimal values and negative string representations are rejected."""
    with pytest.raises(ValueError, match="cannot be negative"):
        validate_non_negative_decimal(Decimal("-10.00"))

    with pytest.raises(ValueError, match="cannot be negative"):
        validate_non_negative_decimal("-10.00")


def test_validate_confidence_score_valid():
    """Verify Decimal objects and valid string representations pass."""
    assert validate_confidence_score(Decimal("0.85")) == Decimal("0.85")
    assert validate_confidence_score("0.85") == Decimal("0.85")
    assert validate_confidence_score(Decimal("0.00")) == Decimal("0.00")
    assert validate_confidence_score(Decimal("1.00")) == Decimal("1.00")


def test_validate_confidence_score_rejects_floats():
    """Verify python float inputs for confidence are explicitly rejected."""
    with pytest.raises(ValueError, match="Float inputs are not allowed for confidence scores"):
        validate_confidence_score(0.85)


def test_validate_confidence_score_out_of_bounds():
    """Verify confidence values outside [0.00, 1.00] are rejected."""
    with pytest.raises(ValueError, match="between 0.00 and 1.00"):
        validate_confidence_score(Decimal("-0.01"))

    with pytest.raises(ValueError, match="between 0.00 and 1.00"):
        validate_confidence_score(Decimal("1.05"))


def test_validate_currency_code():
    """Verify ISO 4217 currency code validation and normalization."""
    assert validate_currency_code("inr") == "INR"
    assert validate_currency_code("USD") == "USD"

    with pytest.raises(ValueError, match="Invalid ISO 4217"):
        validate_currency_code("US")

    with pytest.raises(ValueError, match="Invalid ISO 4217"):
        validate_currency_code("USDT")
