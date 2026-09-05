"""Unit and integration tests for VerificationService and outcome verification."""

from datetime import datetime, timezone
from decimal import Decimal
from uuid import uuid4
import pytest

from app.agents.graph.state import WorkflowStatus
from app.ai.gateway import AIGateway
from app.ai.providers.fake_provider import FakeProvider
from app.application.errors import (
    DuplicateOutcomeError,
    IncidentNotFoundError,
    MerchantNotFoundError,
    TenantMismatchError,
)
from app.application.services.orchestration_service import IncidentOrchestrationService
from app.application.services.verification_service import VerificationService
from app.domain.actions.enums import ActionStatus, ActionType, RiskLevel
from app.domain.actions.models import ActionPlan
from app.domain.execution.enums import ExecutionStatus
from app.domain.execution.models import ExecutionResult
from app.domain.incidents.enums import EvidenceType, IncidentSeverity, IncidentStatus, IncidentType
from app.domain.incidents.models import Evidence, Incident
from app.domain.merchants.models import Merchant
from app.domain.outcomes.enums import OutcomeStatus, OutcomeType, VerificationStatus
from app.domain.policies.enums import PolicyDecision
from app.execution.adapters.simulation_adapter import SimulationExecutionAdapter
from app.execution.executor import ActionExecutor
from app.infrastructure.evidence.deterministic_provider import DeterministicEvidenceProvider
from app.infrastructure.verification.deterministic_provider import (
    DeterministicVerificationEvidenceProvider,
)
from tests.application.fakes import FakeUnitOfWork


def create_sample_merchant(merchant_id=None) -> Merchant:
    return Merchant(
        merchant_id=merchant_id or uuid4(),
        name="Nexus Payments Pvt Ltd",
        currency="INR",
        created_at=datetime.now(timezone.utc),
    )


def create_sample_incident(merchant_id, incident_id=None, revenue_at_risk=Decimal("50000.00"), currency="INR") -> Incident:
    return Incident(
        incident_id=incident_id or uuid4(),
        merchant_id=merchant_id,
        incident_type=IncidentType.PAYMENT_DROP_SPIKE,
        severity=IncidentSeverity.HIGH,
        status=IncidentStatus.ACTION_APPROVED,
        detected_at=datetime.now(timezone.utc),
        revenue_at_risk=revenue_at_risk,
        currency=currency,
        confidence=Decimal("0.90"),
        description="Payment failure rate elevated on primary gateway route",
    )


def create_sample_action_plan(
    incident_id,
    action_type=ActionType.GATEWAY_REROUTE,
    target="gateway_axis_secondary",
    expected_recovery=Decimal("35000.00"),
    status=ActionStatus.COMPLETED,
) -> ActionPlan:
    return ActionPlan(
        action_id=uuid4(),
        incident_id=incident_id,
        action_type=action_type,
        target=target,
        expected_recovery=expected_recovery,
        currency="INR",
        risk_level=RiskLevel.LOW,
        confidence=Decimal("0.85"),
        approval_required=False,
        status=status,
        rationale="Reroute traffic to secondary gateway",
        created_at=datetime.now(timezone.utc),
    )


def create_sample_execution_result(
    merchant_id,
    incident_id,
    action_id,
    action_type=ActionType.GATEWAY_REROUTE,
    status=ExecutionStatus.SIMULATED,
    is_simulated=True,
) -> ExecutionResult:
    return ExecutionResult(
        execution_id=uuid4(),
        merchant_id=merchant_id,
        incident_id=incident_id,
        action_id=action_id,
        provider="test_provider",
        action_type=action_type,
        status=status,
        is_simulated=is_simulated,
        provider_reference=f"ref_{uuid4().hex[:8]}",
        idempotency_key=f"idemp_{action_id}",
        executed_at=datetime.now(timezone.utc),
        details={"mode": "test"},
    )


@pytest.mark.anyio
async def test_verification_service_verified_success_protected_revenue():
    """Verify successful verification for protective action (GATEWAY_REROUTE) transitions incident to RESOLVED."""
    uow = FakeUnitOfWork()
    merchant = create_sample_merchant()
    incident = create_sample_incident(merchant.merchant_id, revenue_at_risk=Decimal("50000.00"))
    plan = create_sample_action_plan(
        incident.incident_id,
        action_type=ActionType.GATEWAY_REROUTE,
        expected_recovery=Decimal("35000.00"),
    )
    exec_result = create_sample_execution_result(merchant.merchant_id, incident.incident_id, plan.action_id)

    await uow.merchants.save(merchant)
    await uow.incidents.save(incident)
    await uow.action_plans.save(plan)

    evidence_provider = DeterministicVerificationEvidenceProvider(
        override_metrics={
            "post_execution_success_rate": 0.98,
            "gateway_status": "healthy",
            "traffic_recovery_ratio": 1.0,
        }
    )
    service = VerificationService(uow=uow, evidence_provider=evidence_provider)

    outcome = await service.verify_execution_outcome(
        merchant_id=merchant.merchant_id,
        incident_id=incident.incident_id,
        action_id=plan.action_id,
        execution_result=exec_result,
        correlation_id="corr-verif-01",
    )

    assert outcome.incident_id == incident.incident_id
    assert outcome.action_id == plan.action_id
    assert outcome.outcome_type == OutcomeType.REVENUE_PROTECTED
    assert outcome.amount == Decimal("35000.00")
    assert outcome.status == OutcomeStatus.VERIFIED

    # Check reference payload data
    ref_data = outcome.reference_data
    assert ref_data["verification_status"] == VerificationStatus.VERIFIED_SUCCESS.value
    assert ref_data["protected_revenue"] == "35000.00"
    assert ref_data["remaining_revenue_at_risk"] == "15000.00"
    assert ref_data["recovery_rate"] == "0.7000"
    assert ref_data["correlation_id"] == "corr-verif-01"

    # Incident transitioned to RESOLVED
    updated_incident = await uow.incidents.get_by_id(incident.incident_id)
    assert updated_incident.status == IncidentStatus.RESOLVED


@pytest.mark.anyio
async def test_verification_service_verified_success_recovered_revenue():
    """Verify successful verification for direct recovery action (RETRY_PAYMENT)."""
    uow = FakeUnitOfWork()
    merchant = create_sample_merchant()
    incident = create_sample_incident(merchant.merchant_id, revenue_at_risk=Decimal("20000.00"))
    plan = create_sample_action_plan(
        incident.incident_id,
        action_type=ActionType.RETRY_PAYMENT,
        expected_recovery=Decimal("18000.00"),
    )
    exec_result = create_sample_execution_result(
        merchant.merchant_id, incident.incident_id, plan.action_id, action_type=ActionType.RETRY_PAYMENT, status=ExecutionStatus.SUCCESS, is_simulated=False
    )

    await uow.merchants.save(merchant)
    await uow.incidents.save(incident)
    await uow.action_plans.save(plan)

    evidence_provider = DeterministicVerificationEvidenceProvider(
        override_metrics={
            "post_execution_success_rate": 0.99,
            "gateway_status": "healthy",
        }
    )
    service = VerificationService(uow=uow, evidence_provider=evidence_provider)

    outcome = await service.verify_execution_outcome(
        merchant_id=merchant.merchant_id,
        incident_id=incident.incident_id,
        action_id=plan.action_id,
        execution_result=exec_result,
    )

    assert outcome.outcome_type == OutcomeType.REVENUE_RECOVERED
    assert outcome.amount == Decimal("18000.00")
    assert outcome.reference_data["recovered_revenue"] == "18000.00"
    assert outcome.reference_data["recovery_rate"] == "0.9000"


@pytest.mark.anyio
async def test_verification_service_verified_failure_when_execution_failed():
    """Verify that a failed execution produces VERIFIED_FAILURE with 0.00 economic impact."""
    uow = FakeUnitOfWork()
    merchant = create_sample_merchant()
    incident = create_sample_incident(merchant.merchant_id, revenue_at_risk=Decimal("50000.00"))
    plan = create_sample_action_plan(incident.incident_id, status=ActionStatus.FAILED)
    exec_result = create_sample_execution_result(
        merchant.merchant_id, incident.incident_id, plan.action_id, status=ExecutionStatus.FAILED
    )

    await uow.merchants.save(merchant)
    await uow.incidents.save(incident)
    await uow.action_plans.save(plan)

    service = VerificationService(uow=uow)
    outcome = await service.verify_execution_outcome(
        merchant_id=merchant.merchant_id,
        incident_id=incident.incident_id,
        action_id=plan.action_id,
        execution_result=exec_result,
    )

    assert outcome.outcome_type == OutcomeType.FAILED_RECOVERY
    assert outcome.amount == Decimal("0.00")
    assert outcome.reference_data["verification_status"] == VerificationStatus.VERIFIED_FAILURE.value
    assert outcome.reference_data["recovered_revenue"] == "0.00"
    assert outcome.reference_data["protected_revenue"] == "0.00"

    # Incident does NOT transition to RESOLVED
    updated_incident = await uow.incidents.get_by_id(incident.incident_id)
    assert updated_incident.status == IncidentStatus.ACTION_APPROVED


@pytest.mark.anyio
async def test_verification_service_verified_failure_when_post_evidence_degraded():
    """Verify that execution succeeded but telemetry shows continued failure produces VERIFIED_FAILURE."""
    uow = FakeUnitOfWork()
    merchant = create_sample_merchant()
    incident = create_sample_incident(merchant.merchant_id, revenue_at_risk=Decimal("50000.00"))
    plan = create_sample_action_plan(incident.incident_id)
    exec_result = create_sample_execution_result(merchant.merchant_id, incident.incident_id, plan.action_id)

    await uow.merchants.save(merchant)
    await uow.incidents.save(incident)
    await uow.action_plans.save(plan)

    evidence_provider = DeterministicVerificationEvidenceProvider(
        override_metrics={
            "post_execution_error_rate": 0.85,
            "gateway_status": "unhealthy",
        }
    )
    service = VerificationService(uow=uow, evidence_provider=evidence_provider)

    outcome = await service.verify_execution_outcome(
        merchant_id=merchant.merchant_id,
        incident_id=incident.incident_id,
        action_id=plan.action_id,
        execution_result=exec_result,
    )

    assert outcome.outcome_type == OutcomeType.FAILED_RECOVERY
    assert outcome.amount == Decimal("0.00")
    assert outcome.reference_data["verification_status"] == VerificationStatus.VERIFIED_FAILURE.value


@pytest.mark.anyio
async def test_verification_service_inconclusive_evidence():
    """Verify inconclusive telemetry produces NO_IMPACT and INCONCLUSIVE verification status."""
    uow = FakeUnitOfWork()
    merchant = create_sample_merchant()
    incident = create_sample_incident(merchant.merchant_id)
    plan = create_sample_action_plan(incident.incident_id)
    exec_result = create_sample_execution_result(merchant.merchant_id, incident.incident_id, plan.action_id)

    await uow.merchants.save(merchant)
    await uow.incidents.save(incident)
    await uow.action_plans.save(plan)

    # Empty metrics -> inconclusive
    evidence_provider = DeterministicVerificationEvidenceProvider(override_metrics={})
    service = VerificationService(uow=uow, evidence_provider=evidence_provider)

    outcome = await service.verify_execution_outcome(
        merchant_id=merchant.merchant_id,
        incident_id=incident.incident_id,
        action_id=plan.action_id,
        execution_result=exec_result,
    )

    assert outcome.outcome_type == OutcomeType.NO_IMPACT
    assert outcome.amount == Decimal("0.00")
    assert outcome.reference_data["verification_status"] == VerificationStatus.INCONCLUSIVE.value


@pytest.mark.anyio
async def test_verification_service_duplicate_outcome_prevention():
    """Verify that verifying an action that already has an Outcome raises DuplicateOutcomeError."""
    uow = FakeUnitOfWork()
    merchant = create_sample_merchant()
    incident = create_sample_incident(merchant.merchant_id)
    plan = create_sample_action_plan(incident.incident_id)
    exec_result = create_sample_execution_result(merchant.merchant_id, incident.incident_id, plan.action_id)

    await uow.merchants.save(merchant)
    await uow.incidents.save(incident)
    await uow.action_plans.save(plan)

    service = VerificationService(uow=uow)

    # First verification passes
    await service.verify_execution_outcome(
        merchant_id=merchant.merchant_id,
        incident_id=incident.incident_id,
        action_id=plan.action_id,
        execution_result=exec_result,
    )

    # Second verification attempt raises DuplicateOutcomeError
    with pytest.raises(DuplicateOutcomeError):
        await service.verify_execution_outcome(
            merchant_id=merchant.merchant_id,
            incident_id=incident.incident_id,
            action_id=plan.action_id,
            execution_result=exec_result,
        )


@pytest.mark.anyio
async def test_verification_service_tenant_isolation():
    """Verify cross-tenant verification attempts raise TenantMismatchError."""
    uow = FakeUnitOfWork()
    merchant_a = create_sample_merchant()
    merchant_b = create_sample_merchant()
    incident_a = create_sample_incident(merchant_a.merchant_id)
    plan_a = create_sample_action_plan(incident_a.incident_id)
    exec_result = create_sample_execution_result(merchant_a.merchant_id, incident_a.incident_id, plan_a.action_id)

    await uow.merchants.save(merchant_a)
    await uow.merchants.save(merchant_b)
    await uow.incidents.save(incident_a)
    await uow.action_plans.save(plan_a)

    service = VerificationService(uow=uow)

    # Merchant B tries to verify Merchant A's outcome
    with pytest.raises(TenantMismatchError):
        await service.verify_execution_outcome(
            merchant_id=merchant_b.merchant_id,
            incident_id=incident_a.incident_id,
            action_id=plan_a.action_id,
            execution_result=exec_result,
        )


@pytest.mark.anyio
async def test_complete_end_to_end_audit_chain():
    """Verify full end-to-end trace: Incident -> Evidence -> Investigation -> Plan -> Policy -> Executor -> Outcome."""
    uow = FakeUnitOfWork()
    merchant = create_sample_merchant()
    incident = create_sample_incident(merchant.merchant_id, revenue_at_risk=Decimal("40000.00"))
    await uow.merchants.save(merchant)
    await uow.incidents.save(incident)

    # 1. AI Gateway & Orchestration (Investigation -> Plan -> Policy)
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
        # Expected recovery ratio 0.75 = 30,000 INR (<= 50,000 auto-allow limit -> Policy ALLOW)
        return (
            '{"action_type": "gateway_reroute", '
            '"target": "gateway_axis_secondary", '
            '"expected_recovery_ratio": 0.75, '
            '"risk_level": "low", '
            '"confidence": 0.85, '
            '"rationale": "Reroute traffic to secondary gateway."}'
        )

    provider.generate_structured_json = dynamic_generate_json
    gateway = AIGateway(provider=provider, default_model="gpt-4o-mini")
    diag_evidence_provider = DeterministicEvidenceProvider()
    orchestration_svc = IncidentOrchestrationService(
        uow=uow,
        gateway=gateway,
        evidence_provider=diag_evidence_provider,
    )

    correlation_id = "corr-audit-chain-101"
    orch_result = await orchestration_svc.run_investigation_workflow(
        incident_id=incident.incident_id,
        correlation_id=correlation_id,
    )

    assert orch_result["status"] == WorkflowStatus.COMPLETED
    assert orch_result["policy_decision"].decision == PolicyDecision.ALLOW
    action_plan = orch_result["proposed_action"]
    assert action_plan.status == ActionStatus.APPROVED

    # 2. Execution Layer
    executor = ActionExecutor(uow=uow, provider=SimulationExecutionAdapter())
    exec_result = await executor.execute_action(
        merchant_id=merchant.merchant_id,
        incident_id=incident.incident_id,
        action_id=action_plan.action_id,
        correlation_id=correlation_id,
    )

    assert exec_result.status == ExecutionStatus.SIMULATED
    assert exec_result.is_simulated is True

    # 3. Verification & Outcome Layer
    verif_evidence_provider = DeterministicVerificationEvidenceProvider(
        override_metrics={"post_execution_success_rate": 0.99, "gateway_status": "healthy"}
    )
    verification_svc = VerificationService(uow=uow, evidence_provider=verif_evidence_provider)

    outcome = await verification_svc.verify_execution_outcome(
        merchant_id=merchant.merchant_id,
        incident_id=incident.incident_id,
        action_id=action_plan.action_id,
        execution_result=exec_result,
        correlation_id=correlation_id,
    )

    # 4. Audit Chain Traceability Assertions
    assert outcome.incident_id == incident.incident_id
    assert outcome.action_id == action_plan.action_id
    assert outcome.amount == Decimal("30000.00")
    assert outcome.status == OutcomeStatus.VERIFIED

    ref = outcome.reference_data
    assert ref["merchant_id"] == str(merchant.merchant_id)
    assert ref["incident_id"] == str(incident.incident_id)
    assert ref["action_id"] == str(action_plan.action_id)
    assert ref["execution_id"] == str(exec_result.execution_id)
    assert ref["verification_status"] == VerificationStatus.VERIFIED_SUCCESS.value
    assert ref["recovered_revenue"] == "0.00"
    assert ref["protected_revenue"] == "30000.00"
    assert ref["total_impact"] == "30000.00"
    assert ref["recovery_rate"] == "0.7500"
    assert ref["remaining_revenue_at_risk"] == "10000.00"
    assert ref["correlation_id"] == correlation_id

    # Verify final incident state
    final_incident = await uow.incidents.get_by_id(incident.incident_id)
    assert final_incident.status == IncidentStatus.RESOLVED
