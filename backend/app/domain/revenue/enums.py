"""Revenue domain enums."""

from enum import Enum


class RevenueEventType(str, Enum):
    """Type of financial or revenue event."""

    PAYMENT_SUCCESS = "payment_success"
    PAYMENT_FAILED = "payment_failed"
    REFUND_INITIATED = "refund_initiated"
    REFUND_PROCESSED = "refund_processed"
    DISPUTE_CREATED = "dispute_created"
    SETTLEMENT_PROCESSED = "settlement_processed"
    SUBSCRIPTION_CANCELLED = "subscription_cancelled"
