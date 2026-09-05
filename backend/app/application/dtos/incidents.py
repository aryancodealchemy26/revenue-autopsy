"""Incident use-case DTOs."""

from datetime import datetime
from decimal import Decimal
from typing import Optional
from uuid import UUID, uuid4
from pydantic import BaseModel, Field, field_validator

from app.domain.incidents.enums import IncidentSeverity, IncidentStatus, IncidentType
from app.domain.shared import (
    validate_confidence_score,
    validate_currency_code,
    validate_non_negative_decimal,
    validate_timezone_aware,
)


class CreateIncidentDTO(BaseModel):
    """Use-case input DTO for creating a new Incident."""

    incident_id: UUID = Field(default_factory=uuid4)
    merchant_id: UUID
    incident_type: IncidentType
    severity: IncidentSeverity
    status: IncidentStatus = Field(default=IncidentStatus.DETECTED)
    detected_at: datetime
    revenue_at_risk: Decimal
    currency: str = Field(default="INR")
    confidence: Decimal
    description: str = Field(..., min_length=1)

    @field_validator("detected_at", mode="after")
    @classmethod
    def check_detected_at(cls, v: datetime) -> datetime:
        return validate_timezone_aware(v)

    @field_validator("revenue_at_risk", mode="before")
    @classmethod
    def check_revenue_at_risk(cls, v: object) -> Decimal:
        return validate_non_negative_decimal(v)

    @field_validator("confidence", mode="before")
    @classmethod
    def check_confidence(cls, v: object) -> Decimal:
        return validate_confidence_score(v)

    @field_validator("currency", mode="after")
    @classmethod
    def check_currency(cls, v: str) -> str:
        return validate_currency_code(v)


class UpdateIncidentStatusDTO(BaseModel):
    """Use-case input DTO for updating an Incident's status."""

    new_status: IncidentStatus
