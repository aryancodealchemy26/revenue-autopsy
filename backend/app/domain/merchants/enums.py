"""Merchant domain enums."""

from enum import Enum


class MerchantStatus(str, Enum):
    """Lifecycle status of a merchant."""

    ACTIVE = "active"
    INACTIVE = "inactive"
    SUSPENDED = "suspended"
    ONBOARDING = "onboarding"
