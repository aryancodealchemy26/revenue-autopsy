"""State schema definition for the Revenue Incident LangGraph workflow."""

from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import Any, Dict, List, Optional
from uuid import UUID
from typing_extensions import TypedDict

from app.agents.investigator.schemas import InvestigationResult
from app.domain.actions.models import ActionPlan
from app.domain.incidents.enums import IncidentSeverity, IncidentType
from app.domain.incidents.models import Evidence


class WorkflowStatus(str, Enum):
    """Lifecycle and execution status of the LangGraph agentic workflow."""

    INITIALIZED = "initialized"
    INVESTIGATING = "investigating"
    INVESTIGATION_COMPLETE = "investigation_complete"
    INSUFFICIENT_EVIDENCE = "insufficient_evidence"
    PLANNING = "planning"
    COMPLETED = "completed"
    FAILED = "failed"
    AI_UNAVAILABLE = "ai_unavailable"


class IncidentInvestigationState(TypedDict, total=False):
    """Typed state dictionary passed through the incident response LangGraph workflow.

    Guarantees strict type safety, merchant tenant boundaries, and grounded telemetry.
    """

    # Context & Tenant Isolation
    merchant_id: UUID
    incident_id: UUID
    incident_type: IncidentType
    severity: IncidentSeverity
    detected_at: datetime
    currency: str
    description: str

    # Deterministic Evidence & Financial Quantification
    evidences: List[Evidence]
    baseline_hourly_rate: Optional[Decimal]
    current_hourly_rate: Optional[Decimal]
    duration_hours: Optional[Decimal]
    revenue_at_risk: Decimal

    # Structured Agent Outputs
    investigation: Optional[InvestigationResult]
    proposed_action: Optional[ActionPlan]

    # Workflow Execution Metadata
    status: WorkflowStatus
    error_message: Optional[str]
    correlation_id: Optional[str]
