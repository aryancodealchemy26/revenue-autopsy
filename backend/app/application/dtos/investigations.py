"""Investigation and Evidence use-case DTOs."""

from datetime import datetime
from typing import Any, Dict, List
from uuid import UUID, uuid4
from pydantic import BaseModel, Field, field_validator

from app.domain.incidents.enums import EvidenceType
from app.domain.incidents.models import Evidence, Incident
from app.domain.merchants.models import Merchant
from app.domain.shared import validate_timezone_aware


class CreateEvidenceDTO(BaseModel):
    """Use-case input DTO for creating an Evidence item."""

    evidence_id: UUID = Field(default_factory=uuid4)
    evidence_type: EvidenceType
    source: str = Field(..., min_length=1)
    observed_at: datetime
    summary: str = Field(..., min_length=1)
    metrics_data: Dict[str, Any] = Field(default_factory=dict)

    @field_validator("observed_at", mode="after")
    @classmethod
    def check_observed_at(cls, v: datetime) -> datetime:
        return validate_timezone_aware(v)


class InvestigationContextDTO(BaseModel):
    """Assembled investigation context ready for diagnostic analysis."""

    incident: Incident
    merchant: Merchant
    evidences: List[Evidence]
