"""Schemas for the Revenue Investigator Agent."""

from decimal import Decimal
from typing import List
from uuid import UUID
from pydantic import BaseModel, ConfigDict, Field


class InvestigationResult(BaseModel):
    """Structured, validated diagnostic conclusion from the Revenue Investigator Agent.

    The model reasons strictly over provided evidence and pre-calculated deterministic
    revenue-at-risk. It does NOT generate arbitrary numbers.
    """
    model_config = ConfigDict(frozen=True)

    incident_id: UUID = Field(..., description="ID of the incident under investigation")
    primary_cause: str = Field(..., min_length=5, description="Primary root cause hypothesis")
    secondary_causes: List[str] = Field(default_factory=list, description="Secondary or contributing causes")
    confidence: Decimal = Field(
        ..., ge=Decimal("0.0"), le=Decimal("1.0"), description="Confidence score between 0.0 and 1.0"
    )
    confidence_rationale: str = Field(..., min_length=5, description="Diagnostic rationale for the confidence score")
    affected_cohorts: List[str] = Field(default_factory=list, description="Impacted merchant cohorts or payment routes")
    evidence_keys_used: List[str] = Field(default_factory=list, description="Evidence items or metric sources relied upon")
    is_conclusive: bool = Field(..., description="True if evidence conclusively establishes root cause; False otherwise")
