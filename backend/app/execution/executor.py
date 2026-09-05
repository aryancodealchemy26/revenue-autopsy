"""ActionExecutor service coordinating deterministic, secure execution of approved ActionPlans."""

from datetime import datetime, timezone
import logging
from typing import Optional
from uuid import UUID

from app.application.errors import (
    ActionNotApprovedError,
    ActionPlanNotFoundError,
    DuplicateExecutionError,
    IncidentNotFoundError,
    MerchantNotFoundError,
    TenantMismatchError,
)
from app.application.ports.execution_provider import ExecutionProviderPort
from app.application.ports.unit_of_work import UnitOfWork
from app.application.state_machines import validate_action_transition
from app.domain.actions.enums import ActionStatus
from app.domain.execution.enums import ExecutionStatus
from app.domain.execution.models import ExecutionResult
from app.execution.adapters.composite_adapter import CompositeExecutionAdapter

logger = logging.getLogger(__name__)


class ActionExecutor:
    """Deterministic, secure Executor for approved ActionPlans.

    SECURITY & INTEGRITY BOUNDARIES:
    - AI, Investigator, Planner, and PolicyEngine never execute actions directly.
    - Only ActionExecutor may invoke write-capable execution providers.
    - Requires action status to be strictly APPROVED (rejects PROPOSED, POLICY_CHECK_PENDING, REJECTED).
    - Enforces strict tenant isolation across merchant, incident, and action.
    - Enforces idempotency to guarantee an action is never executed multiple times.
    - Transitions action status safely through APPROVED -> EXECUTING -> COMPLETED / FAILED.
    - Fails closed on any unexpected provider error or timeout.
    """

    def __init__(
        self,
        uow: UnitOfWork,
        provider: Optional[ExecutionProviderPort] = None,
    ):
        self._uow = uow
        self._provider = provider or CompositeExecutionAdapter()

    async def execute_action(
        self,
        merchant_id: UUID,
        incident_id: UUID,
        action_id: UUID,
        correlation_id: Optional[str] = None,
    ) -> ExecutionResult:
        """Execute a previously authorized ActionPlan under strict tenant and state machine guards."""
        async with self._uow:
            # 1. Load entities
            merchant = await self._uow.merchants.get_by_id(merchant_id)
            if not merchant:
                raise MerchantNotFoundError(merchant_id)

            incident = await self._uow.incidents.get_by_id(incident_id)
            if not incident:
                raise IncidentNotFoundError(incident_id)

            action_plan = await self._uow.action_plans.get_by_id(action_id)
            if not action_plan:
                raise ActionPlanNotFoundError(action_id)

            # 2. Strict Tenant Boundaries & Ownership
            if incident.merchant_id != merchant.merchant_id:
                raise TenantMismatchError(
                    f"Incident merchant '{incident.merchant_id}' does not match caller merchant '{merchant.merchant_id}'."
                )

            if action_plan.incident_id != incident.incident_id:
                raise TenantMismatchError(
                    f"Action incident '{action_plan.incident_id}' does not match target incident '{incident.incident_id}'."
                )

            # 3. Validate Action Authorization & Status
            if action_plan.status in (ActionStatus.COMPLETED, ActionStatus.EXECUTING, ActionStatus.FAILED):
                raise DuplicateExecutionError(action_id=action_id, current_status=action_plan.status.value)

            if action_plan.status in (ActionStatus.PROPOSED, ActionStatus.POLICY_CHECK_PENDING, ActionStatus.REJECTED):
                raise ActionNotApprovedError(action_id=action_id, current_status=action_plan.status.value)

            if action_plan.status != ActionStatus.APPROVED:
                raise ActionNotApprovedError(action_id=action_id, current_status=action_plan.status.value)

            # 4. Enforce State Machine Transition to EXECUTING
            validate_action_transition(action_plan.status, ActionStatus.EXECUTING)
            action_plan.status = ActionStatus.EXECUTING
            await self._uow.action_plans.save(action_plan)
            await self._uow.commit()

            # 5. Deterministic Idempotency Key
            idempotency_key = f"exec_{action_plan.action_id}_{int(action_plan.created_at.timestamp())}"

            # 6. Dispatch to Execution Provider (Guarded)
            try:
                result = await self._provider.execute(
                    merchant=merchant,
                    incident=incident,
                    action_plan=action_plan,
                    idempotency_key=idempotency_key,
                    correlation_id=correlation_id,
                )
            except Exception as e:
                logger.exception("Execution provider raised unexpected error for action %s", action_id)
                # Fail-closed
                now = datetime.now(timezone.utc)
                result = ExecutionResult(
                    merchant_id=merchant.merchant_id,
                    incident_id=incident.incident_id,
                    action_id=action_plan.action_id,
                    provider="unknown",
                    action_type=action_plan.action_type,
                    status=ExecutionStatus.FAILED,
                    is_simulated=False,
                    error_message=f"Unhandled provider error: {str(e)}",
                    idempotency_key=idempotency_key,
                    executed_at=now,
                    details={"unhandled_exception": type(e).__name__},
                )

            # 7. Final State Machine Transition based on Execution Result
            if result.status in (ExecutionStatus.SUCCESS, ExecutionStatus.SIMULATED):
                validate_action_transition(action_plan.status, ActionStatus.COMPLETED)
                action_plan.status = ActionStatus.COMPLETED
            else:
                validate_action_transition(action_plan.status, ActionStatus.FAILED)
                action_plan.status = ActionStatus.FAILED

            await self._uow.action_plans.save(action_plan)
            await self._uow.commit()

            return result
