"""Simulation Execution Adapter for actions without a direct Razorpay API equivalent."""

from datetime import datetime, timezone
from typing import Optional
from uuid import uuid4

from app.application.ports.execution_provider import ExecutionProviderPort
from app.domain.actions.enums import ActionType
from app.domain.actions.models import ActionPlan
from app.domain.execution.enums import ExecutionStatus
from app.domain.execution.models import ExecutionResult
from app.domain.incidents.models import Incident
from app.domain.merchants.models import Merchant


class SimulationExecutionAdapter(ExecutionProviderPort):
    """Execution adapter that truthfully simulates mitigation operations in sandbox environments.

    Used for actions that have no direct Razorpay REST API counterpart (e.g. gateway rerouting,
    rate limit adjustments, merchant alerts, webhook resync).
    """

    def __init__(self, provider_name: str = "simulation_adapter"):
        self.provider_name = provider_name

    def supports_action_type(self, action_type: ActionType) -> bool:
        """Simulation adapter supports all recognized domain action types in simulation mode."""
        return True

    async def execute(
        self,
        merchant: Merchant,
        incident: Incident,
        action_plan: ActionPlan,
        idempotency_key: str,
        correlation_id: Optional[str] = None,
    ) -> ExecutionResult:
        """Truthfully record and simulate the mitigation action execution."""
        now = datetime.now(timezone.utc)
        sim_ref = f"sim_{action_plan.action_type.value}_{uuid4().hex[:12]}"

        details = {
            "execution_mode": "simulation",
            "target": action_plan.target,
            "action_type": action_plan.action_type.value,
            "expected_recovery": str(action_plan.expected_recovery),
            "currency": action_plan.currency,
            "correlation_id": correlation_id,
            "notice": "Simulated truthfully; no financial provider writes performed.",
        }

        return ExecutionResult(
            execution_id=uuid4(),
            merchant_id=merchant.merchant_id,
            incident_id=incident.incident_id,
            action_id=action_plan.action_id,
            provider=self.provider_name,
            action_type=action_plan.action_type,
            status=ExecutionStatus.SIMULATED,
            is_simulated=True,
            provider_reference=sim_ref,
            error_message=None,
            idempotency_key=idempotency_key,
            executed_at=now,
            details=details,
        )
