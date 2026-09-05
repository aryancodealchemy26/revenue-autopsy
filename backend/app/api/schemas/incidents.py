"""Pydantic schemas for Incidents, Diagnostic Evidence, and Full Cockpit Context."""

from datetime import datetime
from decimal import Decimal
from typing import Any, Dict, List, Optional
from uuid import UUID
from pydantic import BaseModel, ConfigDict, Field

from app.api.schemas.actions import ActionPlanResponse, ExecutionResultResponse, PolicyEvaluationResponse
from app.api.schemas.outcomes import OutcomeResponse
from app.domain.incidents.enums import EvidenceType, IncidentSeverity, IncidentStatus, IncidentType


class EvidenceResponse(BaseModel):
    """API response schema for an individual diagnostic evidence payload."""

    model_config = ConfigDict(from_attributes=True)

    evidence_id: UUID
    incident_id: UUID
    evidence_type: EvidenceType
    source: str
    observed_at: datetime
    summary: str
    metrics_data: Dict[str, Any] = Field(default_factory=dict)


class InvestigationResultResponse(BaseModel):
    """API response schema for structured AI Investigation findings."""

    model_config = ConfigDict(from_attributes=True)

    incident_id: UUID
    primary_cause: str
    secondary_causes: List[str] = Field(default_factory=list)
    confidence: float
    confidence_rationale: str
    affected_cohorts: List[str] = Field(default_factory=list)
    evidence_keys_used: List[str] = Field(default_factory=list)
    is_conclusive: bool


class IncidentResponse(BaseModel):
    """API response schema for Incident entity."""

    model_config = ConfigDict(from_attributes=True)

    incident_id: UUID
    merchant_id: UUID
    incident_type: IncidentType
    severity: IncidentSeverity
    status: IncidentStatus
    detected_at: datetime
    revenue_at_risk: Decimal = Field(..., max_digits=12, decimal_places=2)
    currency: str = Field(..., min_length=3, max_length=3)
    confidence: Decimal = Field(..., max_digits=3, decimal_places=2)
    description: str


class FullIncidentContextResponse(BaseModel):
    """Aggregated incident cockpit context for full UI cockpit view."""

    model_config = ConfigDict(from_attributes=True)

    incident: IncidentResponse
    evidences: List[EvidenceResponse] = Field(default_factory=list)
    investigation: Optional[InvestigationResultResponse] = None
    proposed_action: Optional[ActionPlanResponse] = None
    policy_decision: Optional[PolicyEvaluationResponse] = None
    execution_result: Optional[ExecutionResultResponse] = None
    outcome: Optional[OutcomeResponse] = None


class RunInvestigationRequest(BaseModel):
    """Request payload for triggering autonomous LangGraph investigation."""

    baseline_hourly_rate: Optional[Decimal] = Field(default=None, max_digits=12, decimal_places=2)
    current_hourly_rate: Optional[Decimal] = Field(default=None, max_digits=12, decimal_places=2)
    duration_hours: Optional[Decimal] = Field(default=None, max_digits=6, decimal_places=2)
    correlation_id: Optional[str] = None


class InvestigationWorkflowResponse(BaseModel):
    """Structured response from LangGraph investigation and recovery planning."""

    model_config = ConfigDict(from_attributes=True)

    incident: IncidentResponse
    investigation: Optional[InvestigationResultResponse] = None
    revenue_at_risk_calculated: Decimal = Field(..., max_digits=12, decimal_places=2)
    proposed_action: Optional[ActionPlanResponse] = None
    policy_decision: Optional[PolicyEvaluationResponse] = None
