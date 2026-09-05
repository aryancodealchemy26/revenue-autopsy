"""Policy domain models."""

from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID, uuid4
from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.domain.policies.enums import PolicyDecision, PolicyRuleCode
from app.domain.shared import validate_timezone_aware


class PolicyRuleResult(BaseModel):
    """Result of evaluating a single deterministic policy rule."""
    model_config = ConfigDict(frozen=True)

    rule_code: PolicyRuleCode
    passed: bool
    decision_impact: PolicyDecision
    message: str
    evaluated_data: Dict[str, Any] = Field(default_factory=dict)


class PolicyEvaluationResult(BaseModel):
    """Structured, auditable authorization decision emitted by the Policy Engine."""
    model_config = ConfigDict(frozen=True)

    decision_id: UUID = Field(default_factory=uuid4)
    action_id: UUID
    incident_id: UUID
    merchant_id: UUID
    decision: PolicyDecision
    reasons: List[str] = Field(default_factory=list)
    rule_results: List[PolicyRuleResult] = Field(default_factory=list)
    evaluated_limits: Dict[str, Any] = Field(default_factory=dict)
    policy_version: str = Field(default="1.0.0")
    evaluated_at: datetime

    @field_validator("evaluated_at", mode="after")
    @classmethod
    def check_evaluated_at(cls, v: datetime) -> datetime:
        return validate_timezone_aware(v)
