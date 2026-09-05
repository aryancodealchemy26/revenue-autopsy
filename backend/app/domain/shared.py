"""Shared domain validators and value object helpers."""

from datetime import datetime
from decimal import Decimal
import re
from typing import Any

CURRENCY_REGEX = re.compile(r"^[A-Z]{3}$")


def validate_timezone_aware(dt: datetime) -> datetime:
    """Ensure datetime object is timezone-aware."""
    if not isinstance(dt, datetime):
        raise ValueError(f"Expected datetime, got {type(dt).__name__}")
    if dt.tzinfo is None or dt.tzinfo.utcoffset(dt) is None:
        raise ValueError("Datetime must be timezone-aware (tzinfo must not be None)")
    return dt


def validate_non_negative_decimal(val: Any) -> Decimal:
    """Ensure monetary input is Decimal or valid string, rejecting float inputs and negative values."""
    if isinstance(val, float):
        raise ValueError("Float inputs are not allowed for monetary amounts. Use Decimal or string representation.")
    if isinstance(val, Decimal):
        dec_val = val
    elif isinstance(val, (int, str)):
        try:
            dec_val = Decimal(str(val))
        except Exception as e:
            raise ValueError(f"Invalid monetary string/number representation: '{val}'") from e
    else:
        raise ValueError(f"Monetary value must be a Decimal or str, got {type(val).__name__}")

    if dec_val < Decimal("0.00"):
        raise ValueError("Monetary amount cannot be negative")
    return dec_val


def validate_confidence_score(val: Any) -> Decimal:
    """Ensure confidence score is Decimal or valid string between 0.00 and 1.00, rejecting float inputs."""
    if isinstance(val, float):
        raise ValueError("Float inputs are not allowed for confidence scores. Use Decimal or string representation.")
    if isinstance(val, Decimal):
        dec_val = val
    elif isinstance(val, (int, str)):
        try:
            dec_val = Decimal(str(val))
        except Exception as e:
            raise ValueError(f"Invalid confidence string/number representation: '{val}'") from e
    else:
        raise ValueError(f"Confidence score must be a Decimal or str, got {type(val).__name__}")

    if dec_val < Decimal("0.00") or dec_val > Decimal("1.00"):
        raise ValueError("Confidence score must be between 0.00 and 1.00")
    return dec_val


def validate_currency_code(currency: str) -> str:
    """Ensure currency is a 3-letter uppercase ISO 4217 code."""
    if not isinstance(currency, str):
        raise ValueError("Currency must be a string")
    normalized = currency.strip().upper()
    if not CURRENCY_REGEX.match(normalized):
        raise ValueError(f"Invalid ISO 4217 currency code: '{currency}'")
    return normalized
