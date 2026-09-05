"""Pydantic schemas for Action Plans, Policy Decisions, and Execution Results."""

from datetime import datetime
from decimal import Decimal
from typing import Any, Dict, List, Optional
from uuid import UUID
from pydantic import BaseModel, ConfigDict, Field

from app.domain.actions.enums import ActionStatus, ActionType, RiskLevel
from app.domain.execution.enums import ExecutionStatus
from app.domain.policies.enums import PolicyDecision, PolicyRuleCode


class ActionPlanResponse(BaseModel):
    """API response schema for ActionPlan entity."""

    model_config = ConfigDict(from_attributes=True)

    action_id: UUID
    incident_id: UUID
    action_type: ActionType
    target: str
    expected_recovery: Decimal = Field(..., max_digits=12, decimal_places=2)
    currency: str = Field(..., min_length=3, max_length=3)
    risk_level: RiskLevel
    confidence: Decimal = Field(..., max_digits=3, decimal_places=2)
    approval_required: bool
    status: ActionStatus
    rationale: str
    created_at: datetime


class PolicyRuleResultResponse(BaseModel):
    """API response schema for an individual policy rule evaluation."""

    model_config = ConfigDict(from_attributes=True)

    rule_code: PolicyRuleCode
    passed: bool
    decision_impact: PolicyDecision
    message: str
    evaluated_data: Dict[str, Any] = Field(default_factory=dict)


class PolicyEvaluationResponse(BaseModel):
    """API response schema for deterministic PolicyEngine evaluation result."""

    model_config = ConfigDict(from_attributes=True)

    decision_id: UUID
    action_id: UUID
    incident_id: UUID
    merchant_id: UUID
    decision: PolicyDecision
    reasons: List[str]
    rule_results: List[PolicyRuleResultResponse]
    evaluated_limits: Dict[str, Any] = Field(default_factory=dict)
    policy_version: str
    evaluated_at: datetime


class AuthorizeActionRequest(BaseModel):
    """Request schema for operator manual sign-off."""

    notes: Optional[str] = Field(default=None, description="Optional operator authorization notes")


class ExecutionResultResponse(BaseModel):
    """API response schema for guarded execution result."""

    model_config = ConfigDict(from_attributes=True)

    execution_id: UUID
    merchant_id: UUID
    incident_id: UUID
    action_id: UUID
    provider: str
    action_type: ActionType
    status: ExecutionStatus
    is_simulated: bool
    provider_reference: Optional[str] = None
    error_message: Optional[str] = None
    idempotency_key: str
    executed_at: datetime
    details: Dict[str, Any] = Field(default_factory=dict)
