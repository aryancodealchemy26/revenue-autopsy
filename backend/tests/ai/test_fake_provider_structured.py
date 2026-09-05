"""Tests for default FakeProvider structured generation contracts."""

from decimal import Decimal
from uuid import uuid4
import pytest

from app.agents.investigator.schemas import InvestigationResult
from app.agents.planner.schemas import RecoveryPlanProposal
from app.ai.gateway import AIGateway
from app.ai.providers.fake_provider import FakeProvider
from app.ai.schemas.messages import ChatMessage, MessageRole
from app.domain.actions.enums import ActionType, RiskLevel


@pytest.mark.anyio
async def test_default_fake_provider_investigation_result_schema():
    """Verify unconfigured FakeProvider produces valid InvestigationResult matching incident context."""
    provider = FakeProvider()
    gateway = AIGateway(provider=provider, default_model="gpt-4o-mini")

    incident_id = uuid4()
    prompt = (
        f"=== INCIDENT CONTEXT ===\n"
        f"Incident ID: {incident_id}\n"
        f"Incident Type: payment_drop_spike\n"
        f"Severity: high\n"
        f"Deterministic Revenue at Risk: INR 45000.00\n"
    )
    messages = [
        ChatMessage(role=MessageRole.system, content="Investigator system prompt"),
        ChatMessage(role=MessageRole.user, content=prompt),
    ]

    result = await gateway.generate_structured(messages=messages, response_model=InvestigationResult)
    assert isinstance(result, InvestigationResult)
    assert result.incident_id == incident_id
    assert "HDFC" in result.primary_cause
    assert result.confidence >= Decimal("0.90")
    assert result.is_conclusive is True
    assert "HDFC_NETBANKING" in result.affected_cohorts


@pytest.mark.anyio
async def test_default_fake_provider_recovery_plan_proposal_schema():
    """Verify unconfigured FakeProvider produces valid RecoveryPlanProposal matching incident context."""
    provider = FakeProvider()
    gateway = AIGateway(provider=provider, default_model="gpt-4o-mini")

    prompt = (
        f"=== INVESTIGATION REPORT ===\n"
        f"Incident Type: payment_drop_spike\n"
        f"Deterministic Revenue at Risk: INR 45000.00\n"
    )
    messages = [
        ChatMessage(role=MessageRole.system, content="Planner system prompt"),
        ChatMessage(role=MessageRole.user, content=prompt),
    ]

    proposal = await gateway.generate_structured(messages=messages, response_model=RecoveryPlanProposal)
    assert isinstance(proposal, RecoveryPlanProposal)
    assert proposal.action_type == ActionType.GATEWAY_REROUTE
    assert proposal.expected_recovery_ratio == Decimal("0.70")
    assert proposal.risk_level == RiskLevel.LOW
    assert proposal.confidence >= Decimal("0.85")


@pytest.mark.anyio
async def test_default_fake_provider_auth_surge_scenario():
    """Verify unconfigured FakeProvider generates high-risk retry proposal for auth surge scenario."""
    provider = FakeProvider()
    gateway = AIGateway(provider=provider, default_model="gpt-4o-mini")

    incident_id = uuid4()
    inv_prompt = f"Incident ID: {incident_id}\nIncident Type: authorization_failure_surge\n"
    messages_inv = [ChatMessage(role=MessageRole.user, content=inv_prompt)]

    inv_result = await gateway.generate_structured(messages=messages_inv, response_model=InvestigationResult)
    assert inv_result.incident_id == incident_id
    assert "Visa" in inv_result.primary_cause or "issuer" in inv_result.primary_cause.lower()

    plan_prompt = f"Incident Type: authorization_failure_surge\n"
    messages_plan = [ChatMessage(role=MessageRole.user, content=plan_prompt)]

    plan_result = await gateway.generate_structured(messages=messages_plan, response_model=RecoveryPlanProposal)
    assert plan_result.action_type == ActionType.RETRY_PAYMENT
    assert plan_result.risk_level == RiskLevel.HIGH
