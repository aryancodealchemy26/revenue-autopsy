"""Deterministic revenue and risk calculations.

All financial arithmetic is executed using standard library Decimal.
The LLM is strictly prohibited from generating, modifying, or approximating
monetary amounts.
"""

from decimal import Decimal, ROUND_HALF_UP
from typing import Any


def calculate_revenue_at_risk(
    baseline_hourly_rate: Decimal,
    current_hourly_rate: Decimal,
    duration_hours: Decimal,
) -> Decimal:
    """Deterministically compute revenue at risk based on anomaly duration and baseline drop.

    Formula:
        loss_per_hour = max(Decimal('0.00'), baseline_hourly_rate - current_hourly_rate)
        revenue_at_risk = loss_per_hour * duration_hours

    Parameters
    ----------
    baseline_hourly_rate : Decimal
        Expected baseline revenue per hour prior to the incident.
    current_hourly_rate : Decimal
        Observed revenue per hour during the incident anomaly.
    duration_hours : Decimal
        Duration of the anomaly window in hours.

    Returns
    -------
    Decimal
        Quantized revenue at risk (2 decimal places).
    """
    if isinstance(baseline_hourly_rate, float) or isinstance(current_hourly_rate, float) or isinstance(duration_hours, float):
        raise TypeError("Float values are strictly prohibited for financial calculations; use Decimal.")

    if duration_hours < Decimal("0.00"):
        raise ValueError("Duration hours cannot be negative.")

    loss_per_hour = max(Decimal("0.00"), baseline_hourly_rate - current_hourly_rate)
    at_risk = loss_per_hour * duration_hours
    return at_risk.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def calculate_expected_recovery(
    revenue_at_risk: Decimal,
    recovery_ratio: Decimal,
) -> Decimal:
    """Deterministically compute expected recovery amount from a recovery ratio.

    Parameters
    ----------
    revenue_at_risk : Decimal
        The quantified revenue at risk.
    recovery_ratio : Decimal
        Estimated recovery proportion (between 0.0 and 1.0).

    Returns
    -------
    Decimal
        Quantized expected recovery amount.
    """
    if isinstance(revenue_at_risk, float) or isinstance(recovery_ratio, float):
        raise TypeError("Float values are strictly prohibited for financial calculations; use Decimal.")

    if recovery_ratio < Decimal("0.00") or recovery_ratio > Decimal("1.00"):
        raise ValueError(f"Recovery ratio must be between 0.00 and 1.00, got {recovery_ratio}")

    expected = revenue_at_risk * recovery_ratio
    return expected.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
