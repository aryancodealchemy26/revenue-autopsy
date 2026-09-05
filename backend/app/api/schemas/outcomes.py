"""Pydantic schemas for verified Economic Outcomes."""

from datetime import datetime
from decimal import Decimal
from typing import Any, Dict
from uuid import UUID
from pydantic import BaseModel, ConfigDict, Field

from app.domain.outcomes.enums import OutcomeStatus, OutcomeType


class OutcomeResponse(BaseModel):
    """API response schema for measured and verified Economic Outcome."""

    model_config = ConfigDict(from_attributes=True)

    outcome_id: UUID
    incident_id: UUID
    action_id: UUID
    outcome_type: OutcomeType
    amount: Decimal = Field(..., max_digits=12, decimal_places=2)
    currency: str = Field(..., min_length=3, max_length=3)
    status: OutcomeStatus
    measured_at: datetime
    reference_data: Dict[str, Any] = Field(default_factory=dict)
