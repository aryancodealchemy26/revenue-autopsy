"""Revenue domain models."""

from datetime import datetime
from decimal import Decimal
from typing import Any, Dict
from uuid import UUID, uuid4
from pydantic import BaseModel, Field, field_validator

from app.domain.revenue.enums import RevenueEventType
from app.domain.shared import (
    validate_currency_code,
    validate_non_negative_decimal,
    validate_timezone_aware,
)


class RevenueEvent(BaseModel):
    """Atomic financial telemetry event impacting merchant revenue."""

    event_id: UUID = Field(default_factory=uuid4)
    merchant_id: UUID
    event_type: RevenueEventType
    source: str = Field(..., min_length=1)
    timestamp: datetime
    amount: Decimal
    currency: str = Field(default="INR")
    metadata: Dict[str, Any] = Field(default_factory=dict)

    @field_validator("timestamp", mode="after")
    @classmethod
    def check_timestamp(cls, v: datetime) -> datetime:
        return validate_timezone_aware(v)

    @field_validator("amount", mode="before")
    @classmethod
    def check_amount(cls, v: Any) -> Decimal:
        return validate_non_negative_decimal(v)

    @field_validator("currency", mode="after")
    @classmethod
    def check_currency(cls, v: str) -> str:
        return validate_currency_code(v)
