"""Incident and Evidence domain models."""

from datetime import datetime
from decimal import Decimal
from typing import Any, Dict
from uuid import UUID, uuid4
from pydantic import BaseModel, Field, field_validator

from app.domain.incidents.enums import (
    EvidenceType,
    IncidentSeverity,
    IncidentStatus,
    IncidentType,
)
from app.domain.shared import (
    validate_confidence_score,
    validate_currency_code,
    validate_non_negative_decimal,
    validate_timezone_aware,
)


class Evidence(BaseModel):
    """Diagnostic evidence item supporting an incident root cause analysis."""

    evidence_id: UUID = Field(default_factory=uuid4)
    incident_id: UUID
    evidence_type: EvidenceType
    source: str = Field(..., min_length=1)
    observed_at: datetime
    summary: str = Field(..., min_length=1)
    metrics_data: Dict[str, Any] = Field(default_factory=dict)

    @field_validator("observed_at", mode="after")
    @classmethod
    def check_observed_at(cls, v: datetime) -> datetime:
        return validate_timezone_aware(v)


class Incident(BaseModel):
    """Revenue incident entity representing a detected anomaly or loss event."""

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
    def check_revenue_at_risk(cls, v: Any) -> Decimal:
        return validate_non_negative_decimal(v)

    @field_validator("confidence", mode="before")
    @classmethod
    def check_confidence(cls, v: Any) -> Decimal:
        return validate_confidence_score(v)

    @field_validator("currency", mode="after")
    @classmethod
    def check_currency(cls, v: str) -> str:
        return validate_currency_code(v)
