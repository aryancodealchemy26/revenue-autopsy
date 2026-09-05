"""Tests for IncidentOrchestrationService."""

from datetime import datetime, timezone
from decimal import Decimal
from uuid import uuid4
import pytest

from app.agents.graph.state import WorkflowStatus
from app.ai.gateway import AIGateway
from app.ai.providers.fake_provider import FakeProvider
from app.application.errors import IncidentNotFoundError, MerchantNotFoundError
from app.application.services.orchestration_service import IncidentOrchestrationService
from app.domain.actions.enums import ActionStatus, ActionType
from app.domain.incidents.enums import IncidentSeverity, IncidentStatus, IncidentType
from app.domain.incidents.models import Incident
from app.domain.merchants.models import Merchant
from app.infrastructure.evidence.deterministic_provider import DeterministicEvidenceProvider
from tests.application.fakes import FakeUnitOfWork


@pytest.mark.anyio
async def test_orchestration_service_end_to_end_success():
    """Verify orchestration service runs workflow, updates statuses, and commits under UoW."""
    uow = FakeUnitOfWork()
    merchant_id = uuid4()
    incident_id = uuid4()

    # Seed merchant and incident
    merchant = Merchant(
        merchant_id=merchant_id,
        name="Test Merchant Ltd",
        currency="INR",
        created_at=datetime.now(timezone.utc),
    )
    incident = Incident(
        incident_id=incident_id,
        merchant_id=merchant_id,
        incident_type=IncidentType.PAYMENT_DROP_SPIKE,
        severity=IncidentSeverity.HIGH,
        status=IncidentStatus.DETECTED,
        detected_at=datetime.now(timezone.utc),
        revenue_at_risk=Decimal("15000.00"),
        currency="INR",
        confidence=Decimal("0.85"),
        description="Payment drop spike detected on primary checkout route",
    )
    await uow.merchants.save(merchant)
    await uow.incidents.save(incident)

    # Provider returns valid investigation then valid planner proposal
    provider = FakeProvider()
    call_count = 0

    async def dynamic_generate_json(*args, **kwargs):
        nonlocal call_count
        call_count += 1
        if call_count == 1:
            return (
                f'{{"incident_id": "{str(incident_id)}", '
                f'"primary_cause": "HDFC netbanking gateway timeout", '
                f'"secondary_causes": [], '
                f'"confidence": 0.90, '
                f'"confidence_rationale": "High error rate in gateway stream.", '
                f'"affected_cohorts": ["HDFC_NETBANKING"], '
                f'"evidence_keys_used": ["ev_1"], '
                f'"is_conclusive": true}}'
            )
        return (
            '{"action_type": "gateway_reroute", '
            '"target": "gateway_axis_secondary", '
            '"expected_recovery_ratio": 0.70, '
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

    result_state = await orchestration_svc.run_investigation_workflow(
        incident_id=incident_id,
        correlation_id="corr-orch-01",
    )

    from app.domain.policies.enums import PolicyDecision

    # Assert workflow result
    assert result_state["status"] == WorkflowStatus.COMPLETED
    assert result_state["investigation"] is not None
    assert result_state["proposed_action"] is not None
    assert result_state["proposed_action"].expected_recovery == Decimal("10500.00")  # 15000 * 0.70
    assert result_state["policy_decision"] is not None
    assert result_state["policy_decision"].decision == PolicyDecision.ALLOW

    # Assert database state updated and committed
    assert uow.committed is True
    updated_incident = await uow.incidents.get_by_id(incident_id)
    assert updated_incident.status == IncidentStatus.ACTION_APPROVED

    saved_plans = await uow.action_plans.list_by_incident(incident_id)
    assert len(saved_plans) == 1
    assert saved_plans[0].action_type == ActionType.GATEWAY_REROUTE
    assert saved_plans[0].status == ActionStatus.APPROVED
    assert saved_plans[0].approval_required is False

    saved_evidence = await uow.evidence.list_by_incident(incident_id)
    assert len(saved_evidence) >= 2


@pytest.mark.anyio
async def test_orchestration_service_missing_incident_raises():
    """Verify IncidentNotFoundError when incident does not exist."""
    uow = FakeUnitOfWork()
    gateway = AIGateway(provider=FakeProvider(), default_model="gpt-4o-mini")
    evidence_provider = DeterministicEvidenceProvider()
    orchestration_svc = IncidentOrchestrationService(
        uow=uow,
        gateway=gateway,
        evidence_provider=evidence_provider,
    )

    non_existent_id = uuid4()
    with pytest.raises(IncidentNotFoundError):
        await orchestration_svc.run_investigation_workflow(incident_id=non_existent_id)


@pytest.mark.anyio
async def test_orchestration_service_missing_merchant_raises():
    """Verify MerchantNotFoundError when associated merchant does not exist."""
    uow = FakeUnitOfWork()
    incident_id = uuid4()
    missing_merchant_id = uuid4()

    incident = Incident(
        incident_id=incident_id,
        merchant_id=missing_merchant_id,
        incident_type=IncidentType.PAYMENT_DROP_SPIKE,
        severity=IncidentSeverity.HIGH,
        status=IncidentStatus.DETECTED,
        detected_at=datetime.now(timezone.utc),
        revenue_at_risk=Decimal("5000.00"),
        currency="INR",
        confidence=Decimal("0.80"),
        description="Orphan incident",
    )
    await uow.incidents.save(incident)

    gateway = AIGateway(provider=FakeProvider(), default_model="gpt-4o-mini")
    evidence_provider = DeterministicEvidenceProvider()
    orchestration_svc = IncidentOrchestrationService(
        uow=uow,
        gateway=gateway,
        evidence_provider=evidence_provider,
    )

    with pytest.raises(MerchantNotFoundError):
        await orchestration_svc.run_investigation_workflow(incident_id=incident_id)
