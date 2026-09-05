"""Outcome domain models."""

from datetime import datetime
from decimal import Decimal
from typing import Any, Dict
from uuid import UUID, uuid4
from pydantic import BaseModel, Field, field_validator

from app.domain.outcomes.enums import OutcomeStatus, OutcomeType
from app.domain.shared import (
    validate_currency_code,
    validate_non_negative_decimal,
    validate_timezone_aware,
)


class Outcome(BaseModel):
    """Outcome entity measuring recovered or protected revenue resulting from an executed action."""

    outcome_id: UUID = Field(default_factory=uuid4)
    incident_id: UUID
    action_id: UUID
    outcome_type: OutcomeType
    amount: Decimal
    currency: str = Field(default="INR")
    status: OutcomeStatus = Field(default=OutcomeStatus.MEASURED)
    measured_at: datetime
    reference_data: Dict[str, Any] = Field(default_factory=dict)

    @field_validator("measured_at", mode="after")
    @classmethod
    def check_measured_at(cls, v: datetime) -> datetime:
        return validate_timezone_aware(v)

    @field_validator("amount", mode="before")
    @classmethod
    def check_amount(cls, v: Any) -> Decimal:
        return validate_non_negative_decimal(v)

    @field_validator("currency", mode="after")
    @classmethod
    def check_currency(cls, v: str) -> str:
        return validate_currency_code(v)
