"""Schemas for the Recovery Planner Agent."""

from decimal import Decimal
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field

from app.domain.actions.enums import ActionType, RiskLevel


class RecoveryPlanProposal(BaseModel):
    """Structured recovery intervention proposal from the Recovery Planner Agent.

    The proposal selects from bounded domain ActionTypes and specifies an estimated
    recovery ratio without directly performing writes or policy authorizations.
    """
    model_config = ConfigDict(frozen=True)

    action_type: ActionType = Field(..., description="Approved domain ActionType for the intervention")
    target: str = Field(..., min_length=1, description="Specific payment route, gateway, or merchant target")
    expected_recovery_ratio: Decimal = Field(
        ...,
        ge=Decimal("0.0"),
        le=Decimal("1.0"),
        description="Estimated ratio of revenue at risk that this action is expected to recover",
    )
    risk_level: RiskLevel = Field(..., description="Assessed operational or business risk level")
    confidence: Decimal = Field(
        ..., ge=Decimal("0.0"), le=Decimal("1.0"), description="Confidence in the proposal's efficacy"
    )
    rationale: str = Field(..., min_length=5, description="Detailed business and engineering rationale")
