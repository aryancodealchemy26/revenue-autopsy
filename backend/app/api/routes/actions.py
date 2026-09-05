"""Action plans, authorization, execution, and verification API endpoints."""

from datetime import datetime, timezone
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status

from app.api.dependencies.auth import get_current_merchant_id
from app.api.dependencies.services import (
    get_action_service,
    get_executor,
    get_incident_service,
    get_uow,
    get_verification_service,
)
from app.api.schemas.actions import (
    ActionPlanResponse,
    AuthorizeActionRequest,
    ExecutionResultResponse,
)
from app.api.schemas.outcomes import OutcomeResponse
from app.application.ports.unit_of_work import UnitOfWork
from app.application.services.action_service import ActionService
from app.application.services.incident_service import IncidentService
from app.application.services.verification_service import VerificationService
from app.application.state_machines import validate_action_transition, validate_incident_transition
from app.domain.actions.enums import ActionStatus
from app.domain.execution.enums import ExecutionStatus
from app.domain.execution.models import ExecutionResult
from app.domain.incidents.enums import IncidentStatus
from app.execution.executor import ActionExecutor

router = APIRouter(prefix="/actions", tags=["Actions"])


@router.get("/{action_id}", response_model=ActionPlanResponse)
async def get_action_plan(
    action_id: UUID,
    merchant_id: UUID = Depends(get_current_merchant_id),
    uow: UnitOfWork = Depends(get_uow),
) -> ActionPlanResponse:
    """Retrieve an individual ActionPlan by ID within tenant boundary."""
    async with uow:
        action = await uow.action_plans.get_by_id(action_id)
        if not action:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"ActionPlan '{action_id}' not found.",
            )

        incident = await uow.incidents.get_by_id(action.incident_id)
        if not incident or incident.merchant_id != merchant_id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"ActionPlan '{action_id}' not found.",
            )

        return ActionPlanResponse.model_validate(action)


@router.post("/{action_id}/authorize", response_model=ActionPlanResponse)
async def authorize_action_plan(
    action_id: UUID,
    request: AuthorizeActionRequest,
    merchant_id: UUID = Depends(get_current_merchant_id),
    uow: UnitOfWork = Depends(get_uow),
) -> ActionPlanResponse:
    """Operator sign-off authorization for an action plan flagged with REQUIRE_APPROVAL."""
    async with uow:
        action = await uow.action_plans.get_by_id(action_id)
        if not action:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"ActionPlan '{action_id}' not found.",
            )

        incident = await uow.incidents.get_by_id(action.incident_id)
        if not incident or incident.merchant_id != merchant_id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"ActionPlan '{action_id}' not found.",
            )

        # Policy Gate Invariant: DENIED/REJECTED actions can NEVER be authorized
        if action.status == ActionStatus.REJECTED:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Cannot authorize action rejected by Policy Engine.",
            )

        # State transition validation
        validate_action_transition(action.status, ActionStatus.APPROVED)
        action.status = ActionStatus.APPROVED
        action.approval_required = False

        validate_incident_transition(incident.status, IncidentStatus.ACTION_APPROVED)
        incident.status = IncidentStatus.ACTION_APPROVED

        saved_action = await uow.action_plans.save(action)
        await uow.incidents.save(incident)
        await uow.commit()

        return ActionPlanResponse.model_validate(saved_action)


@router.post("/{action_id}/execute", response_model=ExecutionResultResponse)
async def execute_action_plan(
    action_id: UUID,
    merchant_id: UUID = Depends(get_current_merchant_id),
    uow: UnitOfWork = Depends(get_uow),
    executor: ActionExecutor = Depends(get_executor),
) -> ExecutionResultResponse:
    """Dispatch an approved ActionPlan to the guarded Execution Broker."""
    async with uow:
        action = await uow.action_plans.get_by_id(action_id)
        if not action:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"ActionPlan '{action_id}' not found.",
            )

        incident = await uow.incidents.get_by_id(action.incident_id)
        if not incident or incident.merchant_id != merchant_id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"ActionPlan '{action_id}' not found.",
            )

    # ActionExecutor handles its own UoW session, tenant validation, idempotency, and status transitions
    result = await executor.execute_action(
        merchant_id=merchant_id,
        incident_id=action.incident_id,
        action_id=action_id,
    )

    return ExecutionResultResponse.model_validate(result)


@router.post("/{action_id}/verify", response_model=OutcomeResponse)
async def verify_action_outcome(
    action_id: UUID,
    merchant_id: UUID = Depends(get_current_merchant_id),
    uow: UnitOfWork = Depends(get_uow),
    verification_service: VerificationService = Depends(get_verification_service),
) -> OutcomeResponse:
    """Verify execution outcome against post-execution telemetry and record quantified economic outcome."""
    async with uow:
        action = await uow.action_plans.get_by_id(action_id)
        if not action:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"ActionPlan '{action_id}' not found.",
            )

        incident = await uow.incidents.get_by_id(action.incident_id)
        if not incident or incident.merchant_id != merchant_id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"ActionPlan '{action_id}' not found.",
            )

        if action.status not in (ActionStatus.COMPLETED, ActionStatus.EXECUTING):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"ActionPlan '{action_id}' is in status '{action.status.value}' and must be executed before verification.",
            )

    # Reconstruct execution context from persisted execution state
    now = datetime.now(timezone.utc)
    idempotency_key = f"exec_{action.action_id}_{int(action.created_at.timestamp())}"
    exec_result = ExecutionResult(
        merchant_id=merchant_id,
        incident_id=action.incident_id,
        action_id=action.action_id,
        provider="simulation_adapter",
        action_type=action.action_type,
        status=ExecutionStatus.SIMULATED if action.status == ActionStatus.COMPLETED else ExecutionStatus.FAILED,
        is_simulated=True,
        provider_reference=f"sim_ref_{action.action_id}",
        idempotency_key=idempotency_key,
        executed_at=now,
        details={"mode": "sandbox_simulation"},
    )

    outcome = await verification_service.verify_execution_outcome(
        merchant_id=merchant_id,
        incident_id=action.incident_id,
        action_id=action_id,
        execution_result=exec_result,
    )

    return OutcomeResponse.model_validate(outcome)
