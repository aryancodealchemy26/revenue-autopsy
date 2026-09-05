"""Economic outcomes API endpoints."""

from typing import List
from uuid import UUID
from fastapi import APIRouter, Depends, Query

from app.api.dependencies.auth import get_current_merchant_id
from app.api.dependencies.services import get_uow
from app.api.schemas.outcomes import OutcomeResponse
from app.application.ports.unit_of_work import UnitOfWork

router = APIRouter(prefix="/outcomes", tags=["Outcomes"])


@router.get("", response_model=List[OutcomeResponse])
async def list_outcomes(
    limit: int = Query(50, ge=1, le=100),
    merchant_id: UUID = Depends(get_current_merchant_id),
    uow: UnitOfWork = Depends(get_uow),
) -> List[OutcomeResponse]:
    """List all verified economic outcomes for the current merchant."""
    async with uow:
        incidents = await uow.incidents.list_by_merchant(merchant_id, limit=limit)
        outcomes: List[OutcomeResponse] = []

        for incident in incidents:
            actions = await uow.action_plans.list_by_incident(incident.incident_id)
            for action in actions:
                outcome = await uow.outcomes.get_by_action_id(action.action_id)
                if outcome:
                    outcomes.append(OutcomeResponse.model_validate(outcome))

        return outcomes
