"""Execution domain models."""

from datetime import datetime
from typing import Any, Dict, Optional
from uuid import UUID, uuid4
from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.domain.actions.enums import ActionType
from app.domain.execution.enums import ExecutionStatus
from app.domain.shared import validate_timezone_aware


class ExecutionResult(BaseModel):
    """Structured, auditable result of an ActionPlan execution attempt."""

    model_config = ConfigDict(frozen=True)

    execution_id: UUID = Field(default_factory=uuid4)
    merchant_id: UUID
    incident_id: UUID
    action_id: UUID
    provider: str = Field(..., min_length=1)
    action_type: ActionType
    status: ExecutionStatus
    is_simulated: bool = False
    provider_reference: Optional[str] = None
    error_message: Optional[str] = None
    idempotency_key: str = Field(..., min_length=1)
    executed_at: datetime
    details: Dict[str, Any] = Field(default_factory=dict)

    @field_validator("executed_at", mode="after")
    @classmethod
    def check_executed_at(cls, v: datetime) -> datetime:
        return validate_timezone_aware(v)
