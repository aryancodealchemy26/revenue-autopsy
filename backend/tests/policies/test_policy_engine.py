"""Comprehensive deterministic unit and integration tests for Policy Engine."""

from datetime import datetime, timezone
from decimal import Decimal
from uuid import uuid4
import pytest

from app.agents.graph.state import WorkflowStatus
from app.ai.gateway import AIGateway
from app.ai.providers.fake_provider import FakeProvider
from app.application.services.orchestration_service import IncidentOrchestrationService
from app.domain.actions.enums import ActionStatus, ActionType, RiskLevel
from app.domain.actions.models import ActionPlan
from app.domain.incidents.enums import IncidentSeverity, IncidentStatus, IncidentType
from app.domain.incidents.models import Incident
from app.domain.merchants.models import Merchant
from app.domain.policies.enums import PolicyDecision, PolicyRuleCode
from app.infrastructure.evidence.deterministic_provider import DeterministicEvidenceProvider
from app.policies.engine import DeterministicPolicyEngine
from tests.application.fakes import FakeUnitOfWork


def create_sample_merchant(merchant_id=None) -> Merchant:
    return Merchant(
        merchant_id=merchant_id or uuid4(),
        name="Acme Payments Pvt Ltd",
        currency="INR",
        created_at=datetime.now(timezone.utc),
    )


def create_sample_incident(merchant_id, incident_id=None, revenue_at_risk=Decimal("50000.00"), currency="INR") -> Incident:
    return Incident(
        incident_id=incident_id or uuid4(),
        merchant_id=merchant_id,
        incident_type=IncidentType.PAYMENT_DROP_SPIKE,
        severity=IncidentSeverity.HIGH,
        status=IncidentStatus.INVESTIGATING,
        detected_at=datetime.now(timezone.utc),
        revenue_at_risk=revenue_at_risk,
        currency=currency,
        confidence=Decimal("0.90"),
        description="High drop spike on primary gateway",
    )


def create_sample_action_plan(
    incident_id,
    action_type=ActionType.GATEWAY_REROUTE,
    target="gateway_hdfc_backup",
    expected_recovery=Decimal("15000.00"),
    currency="INR",
    risk_level=RiskLevel.LOW,
    confidence=Decimal("0.85"),
) -> ActionPlan:
    return ActionPlan(
        action_id=uuid4(),
        incident_id=incident_id,
        action_type=action_type,
        target=target,
        expected_recovery=expected_recovery,
        currency=currency,
        risk_level=risk_level,
        confidence=confidence,
        approval_required=True,
        status=ActionStatus.PROPOSED,
        rationale="Reroute traffic to healthy backup gateway",
        created_at=datetime.now(timezone.utc),
    )


@pytest.mark.anyio
async def test_policy_engine_allow_low_risk_within_limits():
    """Verify low-risk action plan with valid confidence and reasonable recovery is ALLOWED."""
    engine = DeterministicPolicyEngine()
    merchant = create_sample_merchant()
    incident = create_sample_incident(merchant.merchant_id, revenue_at_risk=Decimal("20000.00"))
    plan = create_sample_action_plan(
        incident.incident_id,
        expected_recovery=Decimal("10000.00"),
        risk_level=RiskLevel.LOW,
        confidence=Decimal("0.85"),
    )

    result = await engine.evaluate_action_plan(merchant, incident, plan)

    assert result.decision == PolicyDecision.ALLOW
    assert result.action_id == plan.action_id
    assert result.incident_id == incident.incident_id
    assert result.merchant_id == merchant.merchant_id
    assert len(result.rule_results) >= 5
    assert all(r.passed for r in result.rule_results)
    assert result.policy_version == "1.0.0"


@pytest.mark.anyio
async def test_policy_engine_require_approval_high_risk():
    """Verify high risk action plans always REQUIRE_APPROVAL."""
    engine = DeterministicPolicyEngine()
    merchant = create_sample_merchant()
    incident = create_sample_incident(merchant.merchant_id, revenue_at_risk=Decimal("20000.00"))
    plan = create_sample_action_plan(
        incident.incident_id,
        expected_recovery=Decimal("5000.00"),
        risk_level=RiskLevel.HIGH,
        confidence=Decimal("0.90"),
    )

    result = await engine.evaluate_action_plan(merchant, incident, plan)

    assert result.decision == PolicyDecision.REQUIRE_APPROVAL
    risk_rules = [r for r in result.rule_results if r.rule_code == PolicyRuleCode.RISK_THRESHOLD]
    assert len(risk_rules) == 1
    assert risk_rules[0].decision_impact == PolicyDecision.REQUIRE_APPROVAL


@pytest.mark.anyio
async def test_policy_engine_require_approval_monetary_auto_allow_exceeded():
    """Verify recovery above auto-allow limit (50,000) but below cap REQUIRES_APPROVAL."""
    engine = DeterministicPolicyEngine()
    merchant = create_sample_merchant()
    incident = create_sample_incident(merchant.merchant_id, revenue_at_risk=Decimal("100000.00"))
    plan = create_sample_action_plan(
        incident.incident_id,
        expected_recovery=Decimal("75000.00"),
        risk_level=RiskLevel.LOW,
        confidence=Decimal("0.90"),
    )

    result = await engine.evaluate_action_plan(merchant, incident, plan)

    assert result.decision == PolicyDecision.REQUIRE_APPROVAL
    monetary_rules = [r for r in result.rule_results if r.rule_code == PolicyRuleCode.MONETARY_LIMIT]
    assert len(monetary_rules) == 1
    assert monetary_rules[0].decision_impact == PolicyDecision.REQUIRE_APPROVAL


@pytest.mark.anyio
async def test_policy_engine_require_approval_medium_risk_exceeds_cap():
    """Verify medium-risk action with recovery above medium cap (25,000) REQUIRES_APPROVAL."""
    engine = DeterministicPolicyEngine()
    merchant = create_sample_merchant()
    incident = create_sample_incident(merchant.merchant_id, revenue_at_risk=Decimal("50000.00"))
    plan = create_sample_action_plan(
        incident.incident_id,
        expected_recovery=Decimal("30000.00"),
        risk_level=RiskLevel.MEDIUM,
        confidence=Decimal("0.85"),
    )

    result = await engine.evaluate_action_plan(merchant, incident, plan)

    assert result.decision == PolicyDecision.REQUIRE_APPROVAL
    risk_rules = [r for r in result.rule_results if r.rule_code == PolicyRuleCode.RISK_THRESHOLD]
    assert risk_rules[0].decision_impact == PolicyDecision.REQUIRE_APPROVAL


@pytest.mark.anyio
async def test_policy_engine_require_approval_moderate_confidence():
    """Verify confidence between 0.40 and 0.70 REQUIRES_APPROVAL."""
    engine = DeterministicPolicyEngine()
    merchant = create_sample_merchant()
    incident = create_sample_incident(merchant.merchant_id, revenue_at_risk=Decimal("20000.00"))
    plan = create_sample_action_plan(
        incident.incident_id,
        expected_recovery=Decimal("5000.00"),
        risk_level=RiskLevel.LOW,
        confidence=Decimal("0.55"),
    )

    result = await engine.evaluate_action_plan(merchant, incident, plan)

    assert result.decision == PolicyDecision.REQUIRE_APPROVAL
    conf_rules = [r for r in result.rule_results if r.rule_code == PolicyRuleCode.CONFIDENCE_THRESHOLD]
    assert conf_rules[0].decision_impact == PolicyDecision.REQUIRE_APPROVAL


@pytest.mark.anyio
async def test_policy_engine_deny_exceeds_absolute_cap():
    """Verify recovery exceeding absolute cap (500,000) is DENIED."""
    engine = DeterministicPolicyEngine()
    merchant = create_sample_merchant()
    incident = create_sample_incident(merchant.merchant_id, revenue_at_risk=Decimal("1000000.00"))
    plan = create_sample_action_plan(
        incident.incident_id,
        expected_recovery=Decimal("600000.00"),
        risk_level=RiskLevel.LOW,
        confidence=Decimal("0.90"),
    )

    result = await engine.evaluate_action_plan(merchant, incident, plan)

    assert result.decision == PolicyDecision.DENY
    monetary_rules = [r for r in result.rule_results if r.rule_code == PolicyRuleCode.MONETARY_LIMIT]
    assert monetary_rules[0].passed is False
    assert monetary_rules[0].decision_impact == PolicyDecision.DENY


@pytest.mark.anyio
async def test_policy_engine_deny_low_confidence():
    """Verify confidence below 0.40 is DENIED."""
    engine = DeterministicPolicyEngine()
    merchant = create_sample_merchant()
    incident = create_sample_incident(merchant.merchant_id, revenue_at_risk=Decimal("20000.00"))
    plan = create_sample_action_plan(
        incident.incident_id,
        expected_recovery=Decimal("5000.00"),
        risk_level=RiskLevel.LOW,
        confidence=Decimal("0.35"),
    )

    result = await engine.evaluate_action_plan(merchant, incident, plan)

    assert result.decision == PolicyDecision.DENY
    conf_rules = [r for r in result.rule_results if r.rule_code == PolicyRuleCode.CONFIDENCE_THRESHOLD]
    assert conf_rules[0].passed is False
    assert conf_rules[0].decision_impact == PolicyDecision.DENY


@pytest.mark.anyio
async def test_policy_engine_deny_disallowed_action_type():
    """Verify action types not in the allowlist are DENIED."""
    engine = DeterministicPolicyEngine(
        allowed_action_types={ActionType.GATEWAY_REROUTE, ActionType.MERCHANT_ALERT}
    )
    merchant = create_sample_merchant()
    incident = create_sample_incident(merchant.merchant_id, revenue_at_risk=Decimal("20000.00"))
    plan = create_sample_action_plan(
        incident.incident_id,
        action_type=ActionType.RETRY_PAYMENT,
        expected_recovery=Decimal("5000.00"),
    )

    result = await engine.evaluate_action_plan(merchant, incident, plan)

    assert result.decision == PolicyDecision.DENY
    type_rules = [r for r in result.rule_results if r.rule_code == PolicyRuleCode.ACTION_ALLOWLIST]
    assert type_rules[0].passed is False
    assert type_rules[0].decision_impact == PolicyDecision.DENY


@pytest.mark.anyio
async def test_policy_engine_fail_closed_tenant_isolation_mismatch():
    """Verify mismatch between incident merchant_id and caller merchant is DENIED."""
    engine = DeterministicPolicyEngine()
    merchant = create_sample_merchant()
    different_merchant_id = uuid4()
    incident = create_sample_incident(different_merchant_id)
    plan = create_sample_action_plan(incident.incident_id)

    result = await engine.evaluate_action_plan(merchant, incident, plan)

    assert result.decision == PolicyDecision.DENY
    integrity_rules = [r for r in result.rule_results if r.rule_code == PolicyRuleCode.INPUT_INTEGRITY]
    assert integrity_rules[0].passed is False


@pytest.mark.anyio
async def test_policy_engine_fail_closed_incident_id_mismatch():
    """Verify mismatch between plan incident_id and target incident is DENIED."""
    engine = DeterministicPolicyEngine()
    merchant = create_sample_merchant()
    incident = create_sample_incident(merchant.merchant_id)
    different_incident_id = uuid4()
    plan = create_sample_action_plan(different_incident_id)

    result = await engine.evaluate_action_plan(merchant, incident, plan)

    assert result.decision == PolicyDecision.DENY
    integrity_rules = [r for r in result.rule_results if r.rule_code == PolicyRuleCode.INPUT_INTEGRITY]
    assert integrity_rules[0].passed is False


@pytest.mark.anyio
async def test_policy_engine_fail_closed_currency_mismatch():
    """Verify mismatch between plan currency and incident currency is DENIED."""
    engine = DeterministicPolicyEngine()
    merchant = create_sample_merchant()
    incident = create_sample_incident(merchant.merchant_id, currency="INR")
    plan = create_sample_action_plan(incident.incident_id, currency="USD")

    result = await engine.evaluate_action_plan(merchant, incident, plan)

    assert result.decision == PolicyDecision.DENY
    integrity_rules = [r for r in result.rule_results if r.rule_code == PolicyRuleCode.INPUT_INTEGRITY]
    assert integrity_rules[0].passed is False


@pytest.mark.anyio
async def test_policy_engine_fail_closed_recovery_exceeds_revenue_at_risk():
    """Verify recovery claiming more than total revenue at risk is DENIED."""
    engine = DeterministicPolicyEngine()
    merchant = create_sample_merchant()
    incident = create_sample_incident(merchant.merchant_id, revenue_at_risk=Decimal("10000.00"))
    plan = create_sample_action_plan(incident.incident_id, expected_recovery=Decimal("15000.00"))

    result = await engine.evaluate_action_plan(merchant, incident, plan)

    assert result.decision == PolicyDecision.DENY
    integrity_rules = [r for r in result.rule_results if r.rule_code == PolicyRuleCode.INPUT_INTEGRITY]
    assert integrity_rules[0].passed is False


@pytest.mark.anyio
async def test_policy_engine_duplicate_action_protection():
    """Verify duplicate active action plans on the same target are DENIED."""
    engine = DeterministicPolicyEngine()
    merchant = create_sample_merchant()
    incident = create_sample_incident(merchant.merchant_id, revenue_at_risk=Decimal("50000.00"))

    existing_action = create_sample_action_plan(
        incident.incident_id,
        action_type=ActionType.GATEWAY_REROUTE,
        target="gateway_axis_backup",
        expected_recovery=Decimal("10000.00"),
    )
    existing_action.status = ActionStatus.EXECUTING

    new_action = create_sample_action_plan(
        incident.incident_id,
        action_type=ActionType.GATEWAY_REROUTE,
        target="gateway_axis_backup",
        expected_recovery=Decimal("10000.00"),
    )

    result = await engine.evaluate_action_plan(
        merchant, incident, new_action, existing_actions=[existing_action]
    )

    assert result.decision == PolicyDecision.DENY
    dup_rules = [r for r in result.rule_results if r.rule_code == PolicyRuleCode.DUPLICATE_PROTECTION]
    assert dup_rules[0].passed is False
    assert dup_rules[0].decision_impact == PolicyDecision.DENY


@pytest.mark.anyio
async def test_policy_engine_allows_when_previous_action_completed():
    """Verify action on target is ALLOWED if prior action was COMPLETED or REJECTED."""
    engine = DeterministicPolicyEngine()
    merchant = create_sample_merchant()
    incident = create_sample_incident(merchant.merchant_id, revenue_at_risk=Decimal("50000.00"))

    past_action = create_sample_action_plan(
        incident.incident_id,
        action_type=ActionType.GATEWAY_REROUTE,
        target="gateway_axis_backup",
        expected_recovery=Decimal("10000.00"),
    )
    past_action.status = ActionStatus.COMPLETED

    new_action = create_sample_action_plan(
        incident.incident_id,
        action_type=ActionType.GATEWAY_REROUTE,
        target="gateway_axis_backup",
        expected_recovery=Decimal("10000.00"),
    )

    result = await engine.evaluate_action_plan(
        merchant, incident, new_action, existing_actions=[past_action]
    )

    assert result.decision == PolicyDecision.ALLOW
    dup_rules = [r for r in result.rule_results if r.rule_code == PolicyRuleCode.DUPLICATE_PROTECTION]
    assert dup_rules[0].passed is True


@pytest.mark.anyio
async def test_orchestration_integration_require_approval():
    """Verify orchestration workflow marks action as POLICY_CHECK_PENDING when approval is required."""
    uow = FakeUnitOfWork()
    merchant = create_sample_merchant()
    incident = create_sample_incident(merchant.merchant_id, revenue_at_risk=Decimal("100000.00"))
    await uow.merchants.save(merchant)
    await uow.incidents.save(incident)

    provider = FakeProvider()
    call_count = 0

    async def dynamic_generate_json(*args, **kwargs):
        nonlocal call_count
        call_count += 1
        if call_count == 1:
            return (
                f'{{"incident_id": "{str(incident.incident_id)}", '
                f'"primary_cause": "HDFC netbanking gateway timeout", '
                f'"secondary_causes": [], '
                f'"confidence": 0.90, '
                f'"confidence_rationale": "High error rate in gateway stream.", '
                f'"affected_cohorts": ["HDFC_NETBANKING"], '
                f'"evidence_keys_used": ["ev_1"], '
                f'"is_conclusive": true}}'
            )
        # High risk action requiring approval
        return (
            '{"action_type": "gateway_reroute", '
            '"target": "gateway_axis_secondary", '
            '"expected_recovery_ratio": 0.80, '
            '"risk_level": "high", '
            '"confidence": 0.85, '
            '"rationale": "High risk gateway reroute."}'
        )

    provider.generate_structured_json = dynamic_generate_json
    gateway = AIGateway(provider=provider, default_model="gpt-4o-mini")
    evidence_provider = DeterministicEvidenceProvider()
    orchestration_svc = IncidentOrchestrationService(
        uow=uow,
        gateway=gateway,
        evidence_provider=evidence_provider,
    )

    result_state = await orchestration_svc.run_investigation_workflow(
        incident_id=incident.incident_id,
        correlation_id="corr-policy-req-appr",
    )

    assert result_state["status"] == WorkflowStatus.COMPLETED
    assert result_state["policy_decision"] is not None
    assert result_state["policy_decision"].decision == PolicyDecision.REQUIRE_APPROVAL

    updated_incident = await uow.incidents.get_by_id(incident.incident_id)
    assert updated_incident.status == IncidentStatus.ACTION_PROPOSED

    saved_plans = await uow.action_plans.list_by_incident(incident.incident_id)
    assert len(saved_plans) == 1
    assert saved_plans[0].status == ActionStatus.POLICY_CHECK_PENDING
    assert saved_plans[0].approval_required is True


@pytest.mark.anyio
async def test_orchestration_integration_denied_action():
    """Verify orchestration workflow marks action as REJECTED when policy DENIES the action."""
    uow = FakeUnitOfWork()
    merchant = create_sample_merchant()
    incident = create_sample_incident(merchant.merchant_id, revenue_at_risk=Decimal("10000.00"))
    await uow.merchants.save(merchant)
    await uow.incidents.save(incident)

    provider = FakeProvider()
    call_count = 0

    async def dynamic_generate_json(*args, **kwargs):
        nonlocal call_count
        call_count += 1
        if call_count == 1:
            return (
                f'{{"incident_id": "{str(incident.incident_id)}", '
                f'"primary_cause": "HDFC netbanking gateway timeout", '
                f'"secondary_causes": [], '
                f'"confidence": 0.90, '
                f'"confidence_rationale": "High error rate in gateway stream.", '
                f'"affected_cohorts": ["HDFC_NETBANKING"], '
                f'"evidence_keys_used": ["ev_1"], '
                f'"is_conclusive": true}}'
            )
        # Low confidence action that policy will DENY
        return (
            '{"action_type": "gateway_reroute", '
            '"target": "gateway_axis_secondary", '
            '"expected_recovery_ratio": 0.50, '
            '"risk_level": "low", '
            '"confidence": 0.30, '
            '"rationale": "Very low confidence proposed action."}'
        )

    provider.generate_structured_json = dynamic_generate_json
    gateway = AIGateway(provider=provider, default_model="gpt-4o-mini")
    evidence_provider = DeterministicEvidenceProvider()
    orchestration_svc = IncidentOrchestrationService(
        uow=uow,
        gateway=gateway,
        evidence_provider=evidence_provider,
    )

    result_state = await orchestration_svc.run_investigation_workflow(
        incident_id=incident.incident_id,
        correlation_id="corr-policy-deny",
    )

    assert result_state["status"] == WorkflowStatus.COMPLETED
    assert result_state["policy_decision"] is not None
    assert result_state["policy_decision"].decision == PolicyDecision.DENY

    updated_incident = await uow.incidents.get_by_id(incident.incident_id)
    assert updated_incident.status == IncidentStatus.ACTION_PROPOSED

    saved_plans = await uow.action_plans.list_by_incident(incident.incident_id)
    assert len(saved_plans) == 1
    assert saved_plans[0].status == ActionStatus.REJECTED
