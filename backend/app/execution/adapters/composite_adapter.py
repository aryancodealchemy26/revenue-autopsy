"""Composite Execution Adapter routing actions to either Razorpay Test Mode or Simulation."""

from typing import Optional

from app.application.ports.execution_provider import ExecutionProviderPort
from app.domain.actions.enums import ActionType
from app.domain.actions.models import ActionPlan
from app.domain.execution.models import ExecutionResult
from app.domain.incidents.models import Incident
from app.domain.merchants.models import Merchant
from app.execution.adapters.razorpay_adapter import RazorpayTestModeAdapter
from app.execution.adapters.simulation_adapter import SimulationExecutionAdapter


class CompositeExecutionAdapter(ExecutionProviderPort):
    """Router adapter directing actions to supported real provider or simulation sandbox.

    Guarantees:
    - Truthfully supported actions (e.g. RETRY_PAYMENT with configured credentials) go to Razorpay Test Mode.
    - Unsupported actions (e.g. GATEWAY_REROUTE, RATE_LIMIT_ADJUSTMENT) go to SimulationExecutionAdapter.
    """

    def __init__(
        self,
        razorpay_adapter: Optional[RazorpayTestModeAdapter] = None,
        simulation_adapter: Optional[SimulationExecutionAdapter] = None,
    ):
        self.razorpay_adapter = razorpay_adapter or RazorpayTestModeAdapter()
        self.simulation_adapter = simulation_adapter or SimulationExecutionAdapter()

    def supports_action_type(self, action_type: ActionType) -> bool:
        """Composite adapter supports all recognized domain action types (via provider or simulation)."""
        return True

    async def execute(
        self,
        merchant: Merchant,
        incident: Incident,
        action_plan: ActionPlan,
        idempotency_key: str,
        correlation_id: Optional[str] = None,
    ) -> ExecutionResult:
        """Route execution to Razorpay Test Mode if supported & configured, else Simulation."""
        if self.razorpay_adapter.supports_action_type(action_plan.action_type) and self.razorpay_adapter.key_id:
            return await self.razorpay_adapter.execute(
                merchant=merchant,
                incident=incident,
                action_plan=action_plan,
                idempotency_key=idempotency_key,
                correlation_id=correlation_id,
            )

        return await self.simulation_adapter.execute(
            merchant=merchant,
            incident=incident,
            action_plan=action_plan,
            idempotency_key=idempotency_key,
            correlation_id=correlation_id,
        )
