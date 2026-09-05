"""Policy Engine port interface for deterministic authorization and safety evaluation."""

from abc import ABC, abstractmethod
from typing import List, Optional

from app.domain.actions.models import ActionPlan
from app.domain.incidents.models import Incident
from app.domain.merchants.models import Merchant
from app.domain.policies.models import PolicyEvaluationResult


class PolicyEnginePort(ABC):
    """Abstract Port for evaluating candidate ActionPlans against deterministic policies.

    The application layer depends on this abstraction rather than concrete policy rules.
    """

    @abstractmethod
    async def evaluate_action_plan(
        self,
        merchant: Merchant,
        incident: Incident,
        action_plan: ActionPlan,
        existing_actions: Optional[List[ActionPlan]] = None,
        correlation_id: Optional[str] = None,
    ) -> PolicyEvaluationResult:
        """Deterministically evaluate an ActionPlan against security, financial, and risk policies.

        Returns an auditable PolicyEvaluationResult with ALLOW, REQUIRE_APPROVAL, or DENY.
        """
        pass
