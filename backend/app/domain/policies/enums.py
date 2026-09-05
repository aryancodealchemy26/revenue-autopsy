"""Policy domain enums."""

from enum import Enum


class PolicyDecision(str, Enum):
    """Deterministic authorization decision for an ActionPlan."""

    ALLOW = "allow"
    REQUIRE_APPROVAL = "require_approval"
    DENY = "deny"


class PolicyRuleCode(str, Enum):
    """Identifier for individual policy validation rules."""

    INPUT_INTEGRITY = "input_integrity"
    ACTION_ALLOWLIST = "action_allowlist"
    MONETARY_LIMIT = "monetary_limit"
    RISK_THRESHOLD = "risk_threshold"
    CONFIDENCE_THRESHOLD = "confidence_threshold"
    MERCHANT_PERMISSION = "merchant_permission"
    DUPLICATE_PROTECTION = "duplicate_protection"
