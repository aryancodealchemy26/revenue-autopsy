"""Action domain enums."""

from enum import Enum


class ActionType(str, Enum):
    """Type of proposed intervention action."""

    GATEWAY_REROUTE = "gateway_reroute"
    RETRY_PAYMENT = "retry_payment"
    MERCHANT_ALERT = "merchant_alert"
    WEBHOOK_RESYNC = "webhook_resync"
    RATE_LIMIT_ADJUSTMENT = "rate_limit_adjustment"


class RiskLevel(str, Enum):
    """Risk assessment level of an intervention action."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class ActionStatus(str, Enum):
    """Execution status of an action plan."""

    PROPOSED = "proposed"
    POLICY_CHECK_PENDING = "policy_check_pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    EXECUTING = "executing"
    COMPLETED = "completed"
    FAILED = "failed"
