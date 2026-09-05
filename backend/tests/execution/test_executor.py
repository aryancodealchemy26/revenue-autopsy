"""Unit and integration tests for ActionExecutor and execution adapters."""

from datetime import datetime, timezone
from decimal import Decimal
from unittest.mock import AsyncMock
from uuid import uuid4
import httpx
import pytest

from app.application.errors import (
    ActionNotApprovedError,
    ActionPlanNotFoundError,
    DuplicateExecutionError,
    IncidentNotFoundError,
    MerchantNotFoundError,
    TenantMismatchError,
)
from app.domain.actions.enums import ActionStatus, ActionType, RiskLevel
from app.domain.actions.models import ActionPlan
from app.domain.execution.enums import ExecutionStatus
from app.domain.execution.models import ExecutionResult
from app.domain.incidents.enums import IncidentSeverity, IncidentStatus, IncidentType
from app.domain.incidents.models import Incident
from app.domain.merchants.models import Merchant
from app.execution.adapters.composite_adapter import CompositeExecutionAdapter
from app.execution.adapters.razorpay_adapter import RazorpayTestModeAdapter
from app.execution.adapters.simulation_adapter import SimulationExecutionAdapter
from app.execution.executor import ActionExecutor
from tests.application.fakes import FakeUnitOfWork


def create_sample_merchant(merchant_id=None) -> Merchant:
    return Merchant(
        merchant_id=merchant_id or uuid4(),
        name="Test Merchant Tech Ltd",
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
        description="Payment drop spike detected",
    )


def create_sample_action_plan(
    incident_id,
    action_type=ActionType.GATEWAY_REROUTE,
    target="gateway_axis_secondary",
    expected_recovery=Decimal("15000.00"),
    status=ActionStatus.APPROVED,
    approval_required=False,
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
        approval_required=approval_required,
        status=status,
        rationale="Automated policy-approved mitigation plan",
        created_at=datetime.now(timezone.utc),
    )


@pytest.mark.anyio
async def test_action_executor_successful_simulation():
    """Verify an approved simulated action executes, transitions to COMPLETED, and returns structured result."""
    uow = FakeUnitOfWork()
    merchant = create_sample_merchant()
    incident = create_sample_incident(merchant.merchant_id)
    plan = create_sample_action_plan(incident.incident_id, action_type=ActionType.GATEWAY_REROUTE, status=ActionStatus.APPROVED)

    await uow.merchants.save(merchant)
    await uow.incidents.save(incident)
    await uow.action_plans.save(plan)

    executor = ActionExecutor(uow=uow, provider=SimulationExecutionAdapter())
    result = await executor.execute_action(
        merchant_id=merchant.merchant_id,
        incident_id=incident.incident_id,
        action_id=plan.action_id,
        correlation_id="corr-sim-01",
    )

    assert result.status == ExecutionStatus.SIMULATED
    assert result.is_simulated is True
    assert result.merchant_id == merchant.merchant_id
    assert result.incident_id == incident.incident_id
    assert result.action_id == plan.action_id
    assert result.provider == "simulation_adapter"
    assert result.provider_reference is not None
    assert result.error_message is None

    # Verify persisted state transitioned to COMPLETED
    updated_plan = await uow.action_plans.get_by_id(plan.action_id)
    assert updated_plan.status == ActionStatus.COMPLETED


@pytest.mark.anyio
async def test_action_executor_rejects_unapproved_status():
    """Verify PROPOSED, POLICY_CHECK_PENDING, and REJECTED plans cannot be executed."""
    for rejected_status in [ActionStatus.PROPOSED, ActionStatus.POLICY_CHECK_PENDING, ActionStatus.REJECTED]:
        uow = FakeUnitOfWork()
        merchant = create_sample_merchant()
        incident = create_sample_incident(merchant.merchant_id)
        plan = create_sample_action_plan(
            incident.incident_id,
            status=rejected_status,
            approval_required=True,
        )

        await uow.merchants.save(merchant)
        await uow.incidents.save(incident)
        await uow.action_plans.save(plan)

        executor = ActionExecutor(uow=uow)
        with pytest.raises(ActionNotApprovedError):
            await executor.execute_action(
                merchant_id=merchant.merchant_id,
                incident_id=incident.incident_id,
                action_id=plan.action_id,
            )


@pytest.mark.anyio
async def test_action_executor_rejects_duplicate_execution():
    """Verify executing an already EXECUTING, COMPLETED, or FAILED action plan raises DuplicateExecutionError."""
    for completed_status in [ActionStatus.EXECUTING, ActionStatus.COMPLETED, ActionStatus.FAILED]:
        uow = FakeUnitOfWork()
        merchant = create_sample_merchant()
        incident = create_sample_incident(merchant.merchant_id)
        plan = create_sample_action_plan(incident.incident_id, status=completed_status)

        await uow.merchants.save(merchant)
        await uow.incidents.save(incident)
        await uow.action_plans.save(plan)

        executor = ActionExecutor(uow=uow)
        with pytest.raises(DuplicateExecutionError):
            await executor.execute_action(
                merchant_id=merchant.merchant_id,
                incident_id=incident.incident_id,
                action_id=plan.action_id,
            )


@pytest.mark.anyio
async def test_action_executor_tenant_mismatch_raises():
    """Verify tenant isolation guards prevent executing actions under wrong merchant or incident."""
    uow = FakeUnitOfWork()
    merchant_a = create_sample_merchant()
    merchant_b = create_sample_merchant()
    incident_a = create_sample_incident(merchant_a.merchant_id)
    plan_a = create_sample_action_plan(incident_a.incident_id)

    await uow.merchants.save(merchant_a)
    await uow.merchants.save(merchant_b)
    await uow.incidents.save(incident_a)
    await uow.action_plans.save(plan_a)

    executor = ActionExecutor(uow=uow)

    # Merchant B tries to execute Merchant A's action
    with pytest.raises(TenantMismatchError):
        await executor.execute_action(
            merchant_id=merchant_b.merchant_id,
            incident_id=incident_a.incident_id,
            action_id=plan_a.action_id,
        )


@pytest.mark.anyio
async def test_action_executor_missing_entity_raises():
    """Verify missing entities raise specific EntityNotFoundError subclasses."""
    uow = FakeUnitOfWork()
    merchant = create_sample_merchant()
    incident = create_sample_incident(merchant.merchant_id)
    await uow.merchants.save(merchant)
    await uow.incidents.save(incident)

    executor = ActionExecutor(uow=uow)

    with pytest.raises(MerchantNotFoundError):
        await executor.execute_action(uuid4(), incident.incident_id, uuid4())

    with pytest.raises(IncidentNotFoundError):
        await executor.execute_action(merchant.merchant_id, uuid4(), uuid4())

    with pytest.raises(ActionPlanNotFoundError):
        await executor.execute_action(merchant.merchant_id, incident.incident_id, uuid4())


@pytest.mark.anyio
async def test_action_executor_provider_failure_fails_closed():
    """Verify when provider fails, action status is transitioned to FAILED and error is recorded."""
    uow = FakeUnitOfWork()
    merchant = create_sample_merchant()
    incident = create_sample_incident(merchant.merchant_id)
    plan = create_sample_action_plan(incident.incident_id, action_type=ActionType.RETRY_PAYMENT)

    await uow.merchants.save(merchant)
    await uow.incidents.save(incident)
    await uow.action_plans.save(plan)

    # Mock provider that returns FAILED
    mock_provider = AsyncMock()
    mock_provider.execute.return_value = ExecutionResult(
        merchant_id=merchant.merchant_id,
        incident_id=incident.incident_id,
        action_id=plan.action_id,
        provider="mock_provider",
        action_type=plan.action_type,
        status=ExecutionStatus.FAILED,
        is_simulated=False,
        error_message="Gateway declined transaction retry.",
        idempotency_key="exec_mock_01",
        executed_at=datetime.now(timezone.utc),
    )

    executor = ActionExecutor(uow=uow, provider=mock_provider)
    result = await executor.execute_action(
        merchant_id=merchant.merchant_id,
        incident_id=incident.incident_id,
        action_id=plan.action_id,
    )

    assert result.status == ExecutionStatus.FAILED
    assert result.error_message == "Gateway declined transaction retry."

    updated_plan = await uow.action_plans.get_by_id(plan.action_id)
    assert updated_plan.status == ActionStatus.FAILED


@pytest.mark.anyio
async def test_action_executor_provider_exception_fails_closed():
    """Verify when provider raises an unhandled exception or timeout, executor fails closed safely."""
    uow = FakeUnitOfWork()
    merchant = create_sample_merchant()
    incident = create_sample_incident(merchant.merchant_id)
    plan = create_sample_action_plan(incident.incident_id)

    await uow.merchants.save(merchant)
    await uow.incidents.save(incident)
    await uow.action_plans.save(plan)

    # Provider that raises
    mock_provider = AsyncMock()
    mock_provider.execute.side_effect = TimeoutError("External provider socket timeout")

    executor = ActionExecutor(uow=uow, provider=mock_provider)
    result = await executor.execute_action(
        merchant_id=merchant.merchant_id,
        incident_id=incident.incident_id,
        action_id=plan.action_id,
    )

    assert result.status == ExecutionStatus.FAILED
    assert "TimeoutError" in result.error_message or "timeout" in result.error_message.lower()

    updated_plan = await uow.action_plans.get_by_id(plan.action_id)
    assert updated_plan.status == ActionStatus.FAILED


@pytest.mark.anyio
async def test_razorpay_test_mode_adapter_success():
    """Verify Razorpay Test Mode adapter creates an order and returns SUCCESS when API succeeds."""
    merchant = create_sample_merchant()
    incident = create_sample_incident(merchant.merchant_id)
    plan = create_sample_action_plan(incident.incident_id, action_type=ActionType.RETRY_PAYMENT, expected_recovery=Decimal("2500.00"))

    # Mock HTTP transport
    def mock_handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/v1/orders"
        assert request.headers.get("authorization") is not None
        return httpx.Response(
            status_code=201,
            json={
                "id": "order_test_rzp98765",
                "entity": "order",
                "amount": 250000,
                "currency": "INR",
                "status": "created",
                "created_at": 1700000000,
            },
        )

    transport = httpx.MockTransport(mock_handler)
    http_client = httpx.AsyncClient(transport=transport)

    adapter = RazorpayTestModeAdapter(
        key_id="rzp_test_mockkey123",
        key_secret="mocksecret456",
        http_client=http_client,
    )

    result = await adapter.execute(
        merchant=merchant,
        incident=incident,
        action_plan=plan,
        idempotency_key="idemp_rzp_01",
    )

    assert result.status == ExecutionStatus.SUCCESS
    assert result.is_simulated is False
    assert result.provider == "razorpay_test_mode"
    assert result.provider_reference == "order_test_rzp98765"
    assert result.error_message is None
    assert result.details["amount"] == 250000


@pytest.mark.anyio
async def test_razorpay_test_mode_adapter_missing_credentials():
    """Verify Razorpay adapter fails closed when credentials are missing."""
    merchant = create_sample_merchant()
    incident = create_sample_incident(merchant.merchant_id)
    plan = create_sample_action_plan(incident.incident_id, action_type=ActionType.RETRY_PAYMENT)

    adapter = RazorpayTestModeAdapter(key_id=None, key_secret=None)
    result = await adapter.execute(merchant, incident, plan, idempotency_key="idemp_missing")

    assert result.status == ExecutionStatus.FAILED
    assert "credentials missing" in result.error_message.lower()


@pytest.mark.anyio
async def test_razorpay_test_mode_adapter_blocks_live_keys():
    """Verify Razorpay adapter rejects any key starting with rzp_live_ to safeguard against real money."""
    merchant = create_sample_merchant()
    incident = create_sample_incident(merchant.merchant_id)
    plan = create_sample_action_plan(incident.incident_id, action_type=ActionType.RETRY_PAYMENT)

    adapter = RazorpayTestModeAdapter(key_id="rzp_live_dangerouskey", key_secret="livesecret")
    result = await adapter.execute(merchant, incident, plan, idempotency_key="idemp_live")

    assert result.status == ExecutionStatus.FAILED
    assert "live mode keys rejected" in result.error_message.lower()


@pytest.mark.anyio
async def test_razorpay_test_mode_adapter_api_error_response():
    """Verify Razorpay API 400 error is cleanly structured and marked as FAILED."""
    merchant = create_sample_merchant()
    incident = create_sample_incident(merchant.merchant_id)
    plan = create_sample_action_plan(incident.incident_id, action_type=ActionType.RETRY_PAYMENT)

    def mock_handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            status_code=400,
            json={
                "error": {
                    "code": "BAD_REQUEST_ERROR",
                    "description": "Amount must be at least 100 paise",
                }
            },
        )

    transport = httpx.MockTransport(mock_handler)
    http_client = httpx.AsyncClient(transport=transport)

    adapter = RazorpayTestModeAdapter(
        key_id="rzp_test_valid",
        key_secret="secret",
        http_client=http_client,
    )

    result = await adapter.execute(merchant, incident, plan, idempotency_key="idemp_err")

    assert result.status == ExecutionStatus.FAILED
    assert "Amount must be at least 100 paise" in result.error_message


@pytest.mark.anyio
async def test_composite_adapter_routes_supported_vs_simulated():
    """Verify CompositeExecutionAdapter routes RETRY_PAYMENT to Razorpay and unsupported actions to Simulation."""
    # Simulation action (GATEWAY_REROUTE)
    merchant = create_sample_merchant()
    incident = create_sample_incident(merchant.merchant_id)
    reroute_plan = create_sample_action_plan(incident.incident_id, action_type=ActionType.GATEWAY_REROUTE)

    composite = CompositeExecutionAdapter()
    result_sim = await composite.execute(merchant, incident, reroute_plan, idempotency_key="idemp_sim")

    assert result_sim.status == ExecutionStatus.SIMULATED
    assert result_sim.is_simulated is True
    assert result_sim.provider == "simulation_adapter"

    # Razorpay action with mock client
    def mock_handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(status_code=201, json={"id": "order_test_comp123"})

    rzp_adapter = RazorpayTestModeAdapter(
        key_id="rzp_test_comp",
        key_secret="secret",
        http_client=httpx.AsyncClient(transport=httpx.MockTransport(mock_handler)),
    )
    composite_with_rzp = CompositeExecutionAdapter(razorpay_adapter=rzp_adapter)

    retry_plan = create_sample_action_plan(incident.incident_id, action_type=ActionType.RETRY_PAYMENT)
    result_rzp = await composite_with_rzp.execute(merchant, incident, retry_plan, idempotency_key="idemp_comp_rzp")

    assert result_rzp.status == ExecutionStatus.SUCCESS
    assert result_rzp.is_simulated is False
    assert result_rzp.provider == "razorpay_test_mode"
    assert result_rzp.provider_reference == "order_test_comp123"


@pytest.mark.anyio
async def test_end_to_end_flow_investigation_to_execution():
    """Verify complete lifecycle: Investigation -> Planning -> Policy (ALLOW) -> Execution (COMPLETED)."""
    from app.ai.gateway import AIGateway
    from app.ai.providers.fake_provider import FakeProvider
    from app.application.services.orchestration_service import IncidentOrchestrationService
    from app.domain.policies.enums import PolicyDecision
    from app.infrastructure.evidence.deterministic_provider import DeterministicEvidenceProvider

    uow = FakeUnitOfWork()
    merchant = create_sample_merchant()
    incident = create_sample_incident(merchant.merchant_id, revenue_at_risk=Decimal("30000.00"))
    await uow.merchants.save(merchant)
    await uow.incidents.save(incident)

    # 1. Setup AI gateway
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
        # Low risk, recovery 15,000 (within 50,000 auto-allow) -> Policy ALLOW
        return (
            '{"action_type": "gateway_reroute", '
            '"target": "gateway_axis_secondary", '
            '"expected_recovery_ratio": 0.50, '
            '"risk_level": "low", '
            '"confidence": 0.85, '
            '"rationale": "Reroute traffic to secondary gateway."}'
        )

    provider.generate_structured_json = dynamic_generate_json
    gateway = AIGateway(provider=provider, default_model="gpt-4o-mini")
    evidence_provider = DeterministicEvidenceProvider()
    orchestration_svc = IncidentOrchestrationService(
        uow=uow,
        gateway=gateway,
        evidence_provider=evidence_provider,
    )

    # 2. Run Orchestration (Investigation -> Planning -> Policy)
    result_state = await orchestration_svc.run_investigation_workflow(
        incident_id=incident.incident_id,
        correlation_id="corr-e2e-exec",
    )

    assert result_state["policy_decision"] is not None
    assert result_state["policy_decision"].decision == PolicyDecision.ALLOW
    proposed_action = result_state["proposed_action"]
    assert proposed_action.status == ActionStatus.APPROVED

    # 3. Execute via ActionExecutor
    executor = ActionExecutor(uow=uow, provider=SimulationExecutionAdapter())
    exec_result = await executor.execute_action(
        merchant_id=merchant.merchant_id,
        incident_id=incident.incident_id,
        action_id=proposed_action.action_id,
        correlation_id="corr-e2e-exec",
    )

    # 4. Verify Execution outcome and persisted invariants
    assert exec_result.status == ExecutionStatus.SIMULATED
    assert exec_result.is_simulated is True
    assert exec_result.action_id == proposed_action.action_id

    final_plan = await uow.action_plans.get_by_id(proposed_action.action_id)
    assert final_plan.status == ActionStatus.COMPLETED
