"""Action domain models."""

from datetime import datetime
from decimal import Decimal
from typing import Any
from uuid import UUID, uuid4
from pydantic import BaseModel, Field, field_validator

from app.domain.actions.enums import ActionStatus, ActionType, RiskLevel
from app.domain.shared import (
    validate_confidence_score,
    validate_currency_code,
    validate_non_negative_decimal,
    validate_timezone_aware,
)


class ActionPlan(BaseModel):
    """Intervention plan model representing a bounded proposed mitigation action."""

    action_id: UUID = Field(default_factory=uuid4)
    incident_id: UUID
    action_type: ActionType
    target: str = Field(..., min_length=1)
    expected_recovery: Decimal
    currency: str = Field(default="INR")
    risk_level: RiskLevel
    confidence: Decimal
    approval_required: bool = True
    status: ActionStatus = Field(default=ActionStatus.PROPOSED)
    rationale: str = Field(..., min_length=1)
    created_at: datetime

    @field_validator("created_at", mode="after")
    @classmethod
    def check_created_at(cls, v: datetime) -> datetime:
        return validate_timezone_aware(v)

    @field_validator("expected_recovery", mode="before")
    @classmethod
    def check_expected_recovery(cls, v: Any) -> Decimal:
        return validate_non_negative_decimal(v)

    @field_validator("confidence", mode="before")
    @classmethod
    def check_confidence(cls, v: Any) -> Decimal:
        return validate_confidence_score(v)

    @field_validator("currency", mode="after")
    @classmethod
    def check_currency(cls, v: str) -> str:
        return validate_currency_code(v)
