"""Deterministic economic calculations for revenue recovery and protection."""

from decimal import Decimal, ROUND_HALF_UP
from typing import NamedTuple


class EconomicImpact(NamedTuple):
    """Immutable calculation result of verified economic impact."""

    recovered_revenue: Decimal
    protected_revenue: Decimal
    total_impact: Decimal
    revenue_at_risk: Decimal
    remaining_revenue_at_risk: Decimal
    recovery_rate: Decimal


def calculate_economic_impact(
    revenue_at_risk: Decimal,
    recovered_amount: Decimal,
    protected_amount: Decimal = Decimal("0.00"),
) -> EconomicImpact:
    """Calculate deterministic revenue recovery, protection, remaining loss, and recovery rate.

    Guarantees:
    - Never returns negative values.
    - Total impact (recovered + protected) is strictly capped at revenue_at_risk.
    - Zero division is safely handled (0.0000 rate when risk is zero).
    - Precision is quantized to standard currency 2 decimal places (amounts) and 4 decimal places (rates).
    """
    two_places = Decimal("0.01")
    four_places = Decimal("0.0001")

    # Guard non-negative inputs
    safe_risk = max(Decimal("0.00"), revenue_at_risk).quantize(two_places, rounding=ROUND_HALF_UP)
    safe_recovered = max(Decimal("0.00"), recovered_amount).quantize(two_places, rounding=ROUND_HALF_UP)
    safe_protected = max(Decimal("0.00"), protected_amount).quantize(two_places, rounding=ROUND_HALF_UP)

    # Bound recovered amount to safe_risk
    bounded_recovered = min(safe_risk, safe_recovered)

    # Bound protected amount so total impact does not exceed safe_risk
    remaining_cap_for_protection = max(Decimal("0.00"), safe_risk - bounded_recovered)
    bounded_protected = min(remaining_cap_for_protection, safe_protected)

    total_impact = (bounded_recovered + bounded_protected).quantize(two_places, rounding=ROUND_HALF_UP)
    remaining_risk = max(Decimal("0.00"), safe_risk - total_impact).quantize(two_places, rounding=ROUND_HALF_UP)

    if safe_risk > Decimal("0.00"):
        recovery_rate = (total_impact / safe_risk).quantize(four_places, rounding=ROUND_HALF_UP)
        recovery_rate = min(Decimal("1.0000"), max(Decimal("0.0000"), recovery_rate))
    else:
        recovery_rate = Decimal("0.0000")

    return EconomicImpact(
        recovered_revenue=bounded_recovered,
        protected_revenue=bounded_protected,
        total_impact=total_impact,
        revenue_at_risk=safe_risk,
        remaining_revenue_at_risk=remaining_risk,
        recovery_rate=recovery_rate,
    )
