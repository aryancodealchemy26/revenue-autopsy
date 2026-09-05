"""Execution Provider Port interface for executing authorized ActionPlans."""

from abc import ABC, abstractmethod
from typing import Optional

from app.domain.actions.enums import ActionType
from app.domain.actions.models import ActionPlan
from app.domain.execution.models import ExecutionResult
from app.domain.incidents.models import Incident
from app.domain.merchants.models import Merchant


class ExecutionProviderPort(ABC):
    """Abstract Port for executing authorized ActionPlans via external providers or simulation."""

    @abstractmethod
    def supports_action_type(self, action_type: ActionType) -> bool:
        """Return True if this provider truthfully supports direct execution of the action type."""
        pass

    @abstractmethod
    async def execute(
        self,
        merchant: Merchant,
        incident: Incident,
        action_plan: ActionPlan,
        idempotency_key: str,
        correlation_id: Optional[str] = None,
    ) -> ExecutionResult:
        """Execute an authorized action plan and return a structured ExecutionResult."""
        pass
