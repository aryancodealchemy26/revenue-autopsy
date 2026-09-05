"""Tests for RecoveryPlannerAgent."""

from decimal import Decimal
from uuid import uuid4
import pytest

from app.agents.investigator.schemas import InvestigationResult
from app.agents.planner.agent import RecoveryPlannerAgent
from app.ai.gateway import AIGateway
from app.ai.providers.fake_provider import FakeProvider
from app.domain.actions.enums import ActionStatus, ActionType, RiskLevel
from app.domain.actions.models import ActionPlan


@pytest.mark.anyio
async def test_recovery_planner_agent_proposal_conversion():
    """Verify RecoveryPlannerAgent parses proposal and deterministically calculates ActionPlan."""
    provider = FakeProvider()
    incident_id = uuid4()

    provider.canned_json = (
        '{"action_type": "gateway_reroute", '
        '"target": "gateway_axis_secondary", '
        '"expected_recovery_ratio": 0.80, '
        '"risk_level": "medium", '
        '"confidence": 0.88, '
        '"rationale": "Reroute traffic from degraded HDFC primary route to healthy Axis route."}'
    )

    gateway = AIGateway(provider=provider, default_model="gpt-4o-mini")
    agent = RecoveryPlannerAgent(gateway=gateway)

    investigation = InvestigationResult(
        incident_id=incident_id,
        primary_cause="HDFC gateway 504 outage",
        secondary_causes=[],
        confidence=Decimal("0.90"),
        confidence_rationale="Corroborated by error rate surge",
        affected_cohorts=["HDFC_NETBANKING"],
        evidence_keys_used=["ev_1"],
        is_conclusive=True,
    )

    revenue_at_risk = Decimal("10000.00")
    plan = await agent.plan_recovery(
        incident_id=incident_id,
        incident_type="payment_drop_spike",
        revenue_at_risk=revenue_at_risk,
        currency="INR",
        investigation=investigation,
        correlation_id="corr-plan-01",
    )

    assert isinstance(plan, ActionPlan)
    assert plan.incident_id == incident_id
    assert plan.action_type == ActionType.GATEWAY_REROUTE
    assert plan.target == "gateway_axis_secondary"
    # Deterministic expected recovery: 10000.00 * 0.80 = 8000.00
    assert plan.expected_recovery == Decimal("8000.00")
    assert plan.risk_level == RiskLevel.MEDIUM
    assert plan.confidence == Decimal("0.88")
    assert plan.approval_required is True
    assert plan.status == ActionStatus.PROPOSED
