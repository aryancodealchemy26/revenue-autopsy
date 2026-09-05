"""Outcome domain enums."""

from enum import Enum


class OutcomeType(str, Enum):
    """Classification of incident intervention outcome."""

    REVENUE_RECOVERED = "revenue_recovered"
    REVENUE_PROTECTED = "revenue_protected"
    PARTIAL_RECOVERY = "partial_recovery"
    NO_IMPACT = "no_impact"
    FAILED_RECOVERY = "failed_recovery"


class OutcomeStatus(str, Enum):
    """Verification status of a measured outcome."""

    MEASURED = "measured"
    VERIFIED = "verified"
    AUDITED = "audited"


class VerificationStatus(str, Enum):
    """Deterministic verification status of an executed action."""

    VERIFIED_SUCCESS = "verified_success"
    VERIFIED_FAILURE = "verified_failure"
    INCONCLUSIVE = "inconclusive"
    PENDING = "pending"
