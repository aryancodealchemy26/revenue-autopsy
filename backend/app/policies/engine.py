"""Deterministic Policy Engine service for revenue intervention authorization."""

from datetime import datetime, timezone
from decimal import Decimal
from typing import Any, Dict, List, Optional, Set
from uuid import UUID, uuid4

from app.application.ports.policy_engine import PolicyEnginePort
from app.domain.actions.enums import ActionStatus, ActionType, RiskLevel
from app.domain.actions.models import ActionPlan
from app.domain.incidents.models import Incident
from app.domain.merchants.models import Merchant
from app.domain.policies.enums import PolicyDecision, PolicyRuleCode
from app.domain.policies.models import PolicyEvaluationResult, PolicyRuleResult


class DeterministicPolicyEngine(PolicyEnginePort):
    """Deterministic, provider-independent Policy Engine.

    Evaluates untrusted ActionPlans against strict security, monetary,
    risk, and merchant boundaries. Guarantees fail-closed behavior on missing
    or invalid inputs.
    """

    def __init__(
        self,
        max_auto_allow_recovery: Decimal = Decimal("50000.00"),
        max_absolute_recovery_cap: Decimal = Decimal("500000.00"),
        medium_risk_auto_allow_cap: Decimal = Decimal("25000.00"),
        min_confidence_auto_allow: Decimal = Decimal("0.70"),
        min_confidence_deny: Decimal = Decimal("0.40"),
        allowed_action_types: Optional[Set[ActionType]] = None,
        policy_version: str = "1.0.0",
    ):
        self.max_auto_allow_recovery = max_auto_allow_recovery
        self.max_absolute_recovery_cap = max_absolute_recovery_cap
        self.medium_risk_auto_allow_cap = medium_risk_auto_allow_cap
        self.min_confidence_auto_allow = min_confidence_auto_allow
        self.min_confidence_deny = min_confidence_deny
        self.allowed_action_types = allowed_action_types or {
            ActionType.GATEWAY_REROUTE,
            ActionType.RETRY_PAYMENT,
            ActionType.MERCHANT_ALERT,
            ActionType.WEBHOOK_RESYNC,
            ActionType.RATE_LIMIT_ADJUSTMENT,
        }
        self.policy_version = policy_version

    async def evaluate_action_plan(
        self,
        merchant: Merchant,
        incident: Incident,
        action_plan: ActionPlan,
        existing_actions: Optional[List[ActionPlan]] = None,
        correlation_id: Optional[str] = None,
    ) -> PolicyEvaluationResult:
        """Evaluate an ActionPlan and return a structured, auditable PolicyEvaluationResult."""
        rule_results: List[PolicyRuleResult] = []
        reasons: List[str] = []
        now = datetime.now(timezone.utc)

        # 1. Input Integrity & Tenant Isolation Rule (Fail-Closed)
        integrity_passed = True
        integrity_errors: List[str] = []

        if action_plan.incident_id != incident.incident_id:
            integrity_passed = False
            integrity_errors.append(
                f"Action incident ID ({action_plan.incident_id}) does not match incident ({incident.incident_id})"
            )

        if incident.merchant_id != merchant.merchant_id:
            integrity_passed = False
            integrity_errors.append(
                f"Incident merchant ID ({incident.merchant_id}) does not match tenant merchant ({merchant.merchant_id})"
            )

        if action_plan.currency != incident.currency:
            integrity_passed = False
            integrity_errors.append(
                f"Action currency ({action_plan.currency}) does not match incident currency ({incident.currency})"
            )

        if action_plan.expected_recovery < Decimal("0.00"):
            integrity_passed = False
            integrity_errors.append("Expected recovery cannot be negative.")

        if action_plan.expected_recovery > incident.revenue_at_risk:
            integrity_passed = False
            integrity_errors.append(
                f"Expected recovery ({action_plan.expected_recovery}) exceeds incident revenue at risk ({incident.revenue_at_risk})"
            )

        if action_plan.confidence < Decimal("0.00") or action_plan.confidence > Decimal("1.00"):
            integrity_passed = False
            integrity_errors.append(f"Confidence score {action_plan.confidence} out of range [0.0, 1.0]")

        if not integrity_passed:
            err_msg = "; ".join(integrity_errors)
            rule_results.append(
                PolicyRuleResult(
                    rule_code=PolicyRuleCode.INPUT_INTEGRITY,
                    passed=False,
                    decision_impact=PolicyDecision.DENY,
                    message=err_msg,
                    evaluated_data={"errors": integrity_errors},
                )
            )
            reasons.append(f"Input integrity validation failed: {err_msg}")
            return PolicyEvaluationResult(
                decision_id=uuid4(),
                action_id=action_plan.action_id,
                incident_id=incident.incident_id,
                merchant_id=merchant.merchant_id,
                decision=PolicyDecision.DENY,
                reasons=reasons,
                rule_results=rule_results,
                evaluated_limits=self._get_limits_snapshot(),
                policy_version=self.policy_version,
                evaluated_at=now,
            )

        rule_results.append(
            PolicyRuleResult(
                rule_code=PolicyRuleCode.INPUT_INTEGRITY,
                passed=True,
                decision_impact=PolicyDecision.ALLOW,
                message="Input integrity and tenant isolation verified.",
            )
        )

        # 2. Action Type Allowlist Rule
        if action_plan.action_type not in self.allowed_action_types:
            rule_results.append(
                PolicyRuleResult(
                    rule_code=PolicyRuleCode.ACTION_ALLOWLIST,
                    passed=False,
                    decision_impact=PolicyDecision.DENY,
                    message=f"Action type '{action_plan.action_type.value}' is not permitted by policy.",
                    evaluated_data={"action_type": action_plan.action_type.value},
                )
            )
            reasons.append(f"Action type '{action_plan.action_type.value}' is disallowed.")
        else:
            rule_results.append(
                PolicyRuleResult(
                    rule_code=PolicyRuleCode.ACTION_ALLOWLIST,
                    passed=True,
                    decision_impact=PolicyDecision.ALLOW,
                    message=f"Action type '{action_plan.action_type.value}' is in allowlist.",
                )
            )

        # 3. Monetary Limits Rule
        if action_plan.expected_recovery > self.max_absolute_recovery_cap:
            rule_results.append(
                PolicyRuleResult(
                    rule_code=PolicyRuleCode.MONETARY_LIMIT,
                    passed=False,
                    decision_impact=PolicyDecision.DENY,
                    message=(
                        f"Expected recovery {action_plan.expected_recovery} exceeds absolute policy cap "
                        f"{self.max_absolute_recovery_cap}."
                    ),
                    evaluated_data={
                        "expected_recovery": str(action_plan.expected_recovery),
                        "cap": str(self.max_absolute_recovery_cap),
                    },
                )
            )
            reasons.append("Expected recovery exceeds maximum absolute allowable cap.")
        elif action_plan.expected_recovery > self.max_auto_allow_recovery:
            rule_results.append(
                PolicyRuleResult(
                    rule_code=PolicyRuleCode.MONETARY_LIMIT,
                    passed=True,
                    decision_impact=PolicyDecision.REQUIRE_APPROVAL,
                    message=(
                        f"Expected recovery {action_plan.expected_recovery} exceeds auto-allow limit "
                        f"{self.max_auto_allow_recovery}; requires manual approval."
                    ),
                    evaluated_data={
                        "expected_recovery": str(action_plan.expected_recovery),
                        "auto_allow_limit": str(self.max_auto_allow_recovery),
                    },
                )
            )
            reasons.append("Monetary value exceeds auto-authorization threshold.")
        else:
            rule_results.append(
                PolicyRuleResult(
                    rule_code=PolicyRuleCode.MONETARY_LIMIT,
                    passed=True,
                    decision_impact=PolicyDecision.ALLOW,
                    message="Monetary recovery amount is within auto-allow threshold.",
                )
            )

        # 4. Risk Level Rule
        if action_plan.risk_level == RiskLevel.HIGH:
            rule_results.append(
                PolicyRuleResult(
                    rule_code=PolicyRuleCode.RISK_THRESHOLD,
                    passed=True,
                    decision_impact=PolicyDecision.REQUIRE_APPROVAL,
                    message="High operational risk interventions require manual authorization.",
                    evaluated_data={"risk_level": action_plan.risk_level.value},
                )
            )
            reasons.append("High operational risk requires human approval.")
        elif action_plan.risk_level == RiskLevel.MEDIUM and action_plan.expected_recovery > self.medium_risk_auto_allow_cap:
            rule_results.append(
                PolicyRuleResult(
                    rule_code=PolicyRuleCode.RISK_THRESHOLD,
                    passed=True,
                    decision_impact=PolicyDecision.REQUIRE_APPROVAL,
                    message=(
                        f"Medium risk action with recovery {action_plan.expected_recovery} exceeds medium risk cap "
                        f"{self.medium_risk_auto_allow_cap}; requires approval."
                    ),
                    evaluated_data={"risk_level": action_plan.risk_level.value},
                )
            )
            reasons.append("Medium risk monetary value requires human approval.")
        else:
            rule_results.append(
                PolicyRuleResult(
                    rule_code=PolicyRuleCode.RISK_THRESHOLD,
                    passed=True,
                    decision_impact=PolicyDecision.ALLOW,
                    message="Risk level acceptable for automatic evaluation.",
                )
            )

        # 5. Confidence Threshold Rule
        if action_plan.confidence < self.min_confidence_deny:
            rule_results.append(
                PolicyRuleResult(
                    rule_code=PolicyRuleCode.CONFIDENCE_THRESHOLD,
                    passed=False,
                    decision_impact=PolicyDecision.DENY,
                    message=(
                        f"Action plan confidence {action_plan.confidence} is below minimum safety threshold "
                        f"{self.min_confidence_deny}."
                    ),
                    evaluated_data={
                        "confidence": str(action_plan.confidence),
                        "min_deny_threshold": str(self.min_confidence_deny),
                    },
                )
            )
            reasons.append("Confidence score is too low for safe execution.")
        elif action_plan.confidence < self.min_confidence_auto_allow:
            rule_results.append(
                PolicyRuleResult(
                    rule_code=PolicyRuleCode.CONFIDENCE_THRESHOLD,
                    passed=True,
                    decision_impact=PolicyDecision.REQUIRE_APPROVAL,
                    message=(
                        f"Action plan confidence {action_plan.confidence} is below auto-allow threshold "
                        f"{self.min_confidence_auto_allow}; requires manual validation."
                    ),
                    evaluated_data={
                        "confidence": str(action_plan.confidence),
                        "auto_allow_threshold": str(self.min_confidence_auto_allow),
                    },
                )
            )
            reasons.append("Moderate confidence requires human verification.")
        else:
            rule_results.append(
                PolicyRuleResult(
                    rule_code=PolicyRuleCode.CONFIDENCE_THRESHOLD,
                    passed=True,
                    decision_impact=PolicyDecision.ALLOW,
                    message="Confidence score satisfies auto-allow criteria.",
                )
            )

        # 6. Duplicate / Idempotency Protection Rule
        if existing_actions:
            active_statuses = {
                ActionStatus.PROPOSED,
                ActionStatus.POLICY_CHECK_PENDING,
                ActionStatus.APPROVED,
                ActionStatus.EXECUTING,
            }
            duplicates = [
                a for a in existing_actions
                if a.action_id != action_plan.action_id
                and a.action_type == action_plan.action_type
                and a.target.strip().lower() == action_plan.target.strip().lower()
                and a.status in active_statuses
            ]
            if duplicates:
                rule_results.append(
                    PolicyRuleResult(
                        rule_code=PolicyRuleCode.DUPLICATE_PROTECTION,
                        passed=False,
                        decision_impact=PolicyDecision.DENY,
                        message=(
                            f"Duplicate active action plan already exists for target '{action_plan.target}' "
                            f"(Action ID: {duplicates[0].action_id}, Status: {duplicates[0].status.value})."
                        ),
                        evaluated_data={
                            "duplicate_action_id": str(duplicates[0].action_id),
                            "target": action_plan.target,
                        },
                    )
                )
                reasons.append("Duplicate active action already exists for the specified target.")
            else:
                rule_results.append(
                    PolicyRuleResult(
                        rule_code=PolicyRuleCode.DUPLICATE_PROTECTION,
                        passed=True,
                        decision_impact=PolicyDecision.ALLOW,
                        message="No duplicate active actions detected.",
                    )
                )
        else:
            rule_results.append(
                PolicyRuleResult(
                    rule_code=PolicyRuleCode.DUPLICATE_PROTECTION,
                    passed=True,
                    decision_impact=PolicyDecision.ALLOW,
                    message="No existing actions to evaluate for duplicates.",
                )
            )

        # 7. Synthesize Final Policy Decision
        final_decision = PolicyDecision.ALLOW
        if any(r.decision_impact == PolicyDecision.DENY for r in rule_results):
            final_decision = PolicyDecision.DENY
        elif any(r.decision_impact == PolicyDecision.REQUIRE_APPROVAL for r in rule_results):
            final_decision = PolicyDecision.REQUIRE_APPROVAL

        if not reasons and final_decision == PolicyDecision.ALLOW:
            reasons.append("All policy, monetary, risk, and authorization rules passed.")

        return PolicyEvaluationResult(
            decision_id=uuid4(),
            action_id=action_plan.action_id,
            incident_id=incident.incident_id,
            merchant_id=merchant.merchant_id,
            decision=final_decision,
            reasons=reasons,
            rule_results=rule_results,
            evaluated_limits=self._get_limits_snapshot(),
            policy_version=self.policy_version,
            evaluated_at=now,
        )

    def _get_limits_snapshot(self) -> Dict[str, Any]:
        return {
            "max_auto_allow_recovery": str(self.max_auto_allow_recovery),
            "max_absolute_recovery_cap": str(self.max_absolute_recovery_cap),
            "medium_risk_auto_allow_cap": str(self.medium_risk_auto_allow_cap),
            "min_confidence_auto_allow": str(self.min_confidence_auto_allow),
            "min_confidence_deny": str(self.min_confidence_deny),
            "policy_version": self.policy_version,
        }
