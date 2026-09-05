"""Tests for deterministic financial calculations."""

from decimal import Decimal
import pytest

from app.domain.revenue.calculations import (
    calculate_expected_recovery,
    calculate_revenue_at_risk,
)


def test_calculate_revenue_at_risk_standard():
    """Verify revenue at risk calculation when baseline exceeds current rate."""
    baseline = Decimal("10000.00")
    current = Decimal("6000.00")
    duration = Decimal("2.5")  # 2.5 hours

    # Loss per hour = 4000.00; total = 10000.00
    at_risk = calculate_revenue_at_risk(baseline, current, duration)
    assert at_risk == Decimal("10000.00")


def test_calculate_revenue_at_risk_no_loss():
    """Verify zero revenue at risk when current rate equals or exceeds baseline."""
    baseline = Decimal("5000.00")
    current = Decimal("6000.00")
    duration = Decimal("3.0")

    at_risk = calculate_revenue_at_risk(baseline, current, duration)
    assert at_risk == Decimal("0.00")


def test_calculate_revenue_at_risk_rejects_floats():
    """Verify TypeError when float inputs are supplied."""
    with pytest.raises(TypeError):
        calculate_revenue_at_risk(100.0, Decimal("50.00"), Decimal("1.0"))  # type: ignore

    with pytest.raises(TypeError):
        calculate_revenue_at_risk(Decimal("100.00"), 50.0, Decimal("1.0"))  # type: ignore

    with pytest.raises(TypeError):
        calculate_revenue_at_risk(Decimal("100.00"), Decimal("50.00"), 1.5)  # type: ignore


def test_calculate_revenue_at_risk_negative_duration_raises():
    """Verify ValueError when negative duration is supplied."""
    with pytest.raises(ValueError):
        calculate_revenue_at_risk(Decimal("100.00"), Decimal("50.00"), Decimal("-1.0"))


def test_calculate_expected_recovery_standard():
    """Verify expected recovery calculation from ratio."""
    at_risk = Decimal("50000.00")
    ratio = Decimal("0.75")

    expected = calculate_expected_recovery(at_risk, ratio)
    assert expected == Decimal("37500.00")


def test_calculate_expected_recovery_bounds():
    """Verify error on out-of-bounds recovery ratio."""
    with pytest.raises(ValueError):
        calculate_expected_recovery(Decimal("100.00"), Decimal("1.25"))

    with pytest.raises(ValueError):
        calculate_expected_recovery(Decimal("100.00"), Decimal("-0.10"))
