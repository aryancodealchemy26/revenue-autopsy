"""Deterministic unit tests for economic impact calculations."""

from decimal import Decimal
import pytest

from app.domain.outcomes.calculator import calculate_economic_impact


def test_calculate_economic_impact_full_recovery():
    """Verify full recovery calculates 100% recovery rate and 0 remaining risk."""
    risk = Decimal("50000.00")
    recovered = Decimal("50000.00")

    impact = calculate_economic_impact(revenue_at_risk=risk, recovered_amount=recovered)

    assert impact.recovered_revenue == Decimal("50000.00")
    assert impact.protected_revenue == Decimal("0.00")
    assert impact.total_impact == Decimal("50000.00")
    assert impact.revenue_at_risk == Decimal("50000.00")
    assert impact.remaining_revenue_at_risk == Decimal("0.00")
    assert impact.recovery_rate == Decimal("1.0000")


def test_calculate_economic_impact_partial_recovery():
    """Verify partial recovery computes exact remaining risk and recovery rate."""
    risk = Decimal("100000.00")
    recovered = Decimal("35000.00")

    impact = calculate_economic_impact(revenue_at_risk=risk, recovered_amount=recovered)

    assert impact.recovered_revenue == Decimal("35000.00")
    assert impact.total_impact == Decimal("35000.00")
    assert impact.remaining_revenue_at_risk == Decimal("65000.00")
    assert impact.recovery_rate == Decimal("0.3500")


def test_calculate_economic_impact_protected_revenue():
    """Verify protected revenue calculations for preventive interventions."""
    risk = Decimal("60000.00")
    protected = Decimal("45000.00")

    impact = calculate_economic_impact(revenue_at_risk=risk, recovered_amount=Decimal("0.00"), protected_amount=protected)

    assert impact.recovered_revenue == Decimal("0.00")
    assert impact.protected_revenue == Decimal("45000.00")
    assert impact.total_impact == Decimal("45000.00")
    assert impact.remaining_revenue_at_risk == Decimal("15000.00")
    assert impact.recovery_rate == Decimal("0.7500")


def test_calculate_economic_impact_combined_recovered_and_protected():
    """Verify combination of recovered and protected revenue."""
    risk = Decimal("100000.00")
    recovered = Decimal("40000.00")
    protected = Decimal("30000.00")

    impact = calculate_economic_impact(revenue_at_risk=risk, recovered_amount=recovered, protected_amount=protected)

    assert impact.recovered_revenue == Decimal("40000.00")
    assert impact.protected_revenue == Decimal("30000.00")
    assert impact.total_impact == Decimal("70000.00")
    assert impact.remaining_revenue_at_risk == Decimal("30000.00")
    assert impact.recovery_rate == Decimal("0.7000")


def test_calculate_economic_impact_capped_at_revenue_at_risk():
    """Verify total impact cannot exceed revenue at risk even if input numbers are higher."""
    risk = Decimal("20000.00")
    recovered = Decimal("25000.00")
    protected = Decimal("10000.00")

    impact = calculate_economic_impact(revenue_at_risk=risk, recovered_amount=recovered, protected_amount=protected)

    assert impact.recovered_revenue == Decimal("20000.00")
    assert impact.protected_revenue == Decimal("0.00")
    assert impact.total_impact == Decimal("20000.00")
    assert impact.remaining_revenue_at_risk == Decimal("0.00")
    assert impact.recovery_rate == Decimal("1.0000")


def test_calculate_economic_impact_negative_inputs_sanitized():
    """Verify negative inputs are guarded and treated as 0."""
    risk = Decimal("10000.00")
    recovered = Decimal("-5000.00")
    protected = Decimal("-2000.00")

    impact = calculate_economic_impact(revenue_at_risk=risk, recovered_amount=recovered, protected_amount=protected)

    assert impact.recovered_revenue == Decimal("0.00")
    assert impact.protected_revenue == Decimal("0.00")
    assert impact.total_impact == Decimal("0.00")
    assert impact.remaining_revenue_at_risk == Decimal("10000.00")
    assert impact.recovery_rate == Decimal("0.0000")


def test_calculate_economic_impact_zero_risk_edge_case():
    """Verify zero revenue at risk handles cleanly without ZeroDivisionError."""
    risk = Decimal("0.00")
    recovered = Decimal("1000.00")

    impact = calculate_economic_impact(revenue_at_risk=risk, recovered_amount=recovered)

    assert impact.recovered_revenue == Decimal("0.00")
    assert impact.protected_revenue == Decimal("0.00")
    assert impact.total_impact == Decimal("0.00")
    assert impact.remaining_revenue_at_risk == Decimal("0.00")
    assert impact.recovery_rate == Decimal("0.0000")
