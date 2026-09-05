"""Tests for InvestigatorAgent."""

from datetime import datetime, timezone
from decimal import Decimal
from uuid import uuid4
import pytest

from app.agents.investigator.agent import InvestigatorAgent
from app.agents.investigator.schemas import InvestigationResult
from app.ai.gateway import AIGateway
from app.ai.providers.fake_provider import FakeProvider
from app.domain.incidents.enums import EvidenceType
from app.domain.incidents.models import Evidence


@pytest.mark.anyio
async def test_investigator_agent_conclusive_investigation():
    """Verify InvestigatorAgent parses structured InvestigationResult from FakeProvider."""
    provider = FakeProvider()
    incident_id = uuid4()
    merchant_id = uuid4()

    provider.canned_json = (
        f'{{"incident_id": "{str(incident_id)}", '
        f'"primary_cause": "HDFC netbanking upstream 504 gateway timeout", '
        f'"secondary_causes": ["High transaction concurrency spike"], '
        f'"confidence": 0.92, '
        f'"confidence_rationale": "Clear 504 gateway telemetry corroborated by core logs.", '
        f'"affected_cohorts": ["HDFC_NETBANKING"], '
        f'"evidence_keys_used": ["telemetry_01", "log_02"], '
        f'"is_conclusive": true}}'
    )

    gateway = AIGateway(provider=provider, default_model="gpt-4o-mini")
    agent = InvestigatorAgent(gateway=gateway)

    evidence_item = Evidence(
        evidence_id=uuid4(),
        incident_id=incident_id,
        evidence_type=EvidenceType.TELEMETRY_METRIC,
        source="gateway_stream",
        observed_at=datetime.now(timezone.utc),
        summary="HDFC netbanking 504 error rate 48%",
        metrics_data={"error_code": 504},
    )

    result = await agent.investigate(
        incident_id=str(incident_id),
        merchant_id=str(merchant_id),
        incident_type="payment_drop_spike",
        severity="high",
        revenue_at_risk=Decimal("15000.00"),
        currency="INR",
        description="Payment success drop on HDFC",
        evidences=[evidence_item],
        correlation_id="corr-inv-01",
    )

    assert isinstance(result, InvestigationResult)
    assert result.primary_cause == "HDFC netbanking upstream 504 gateway timeout"
    assert result.confidence == Decimal("0.92")
    assert result.is_conclusive is True
    assert "HDFC_NETBANKING" in result.affected_cohorts


@pytest.mark.anyio
async def test_investigator_agent_low_confidence_marks_inconclusive():
    """Verify low confidence (< 0.40) automatically forces is_conclusive = False."""
    provider = FakeProvider()
    incident_id = uuid4()
    merchant_id = uuid4()

    provider.canned_json = (
        f'{{"incident_id": "{str(incident_id)}", '
        f'"primary_cause": "Speculative network latency", '
        f'"secondary_causes": [], '
        f'"confidence": 0.25, '
        f'"confidence_rationale": "Insufficient data to verify hypothesis.", '
        f'"affected_cohorts": [], '
        f'"evidence_keys_used": [], '
        f'"is_conclusive": true}}'
    )

    gateway = AIGateway(provider=provider, default_model="gpt-4o-mini")
    agent = InvestigatorAgent(gateway=gateway)

    evidence_item = Evidence(
        evidence_id=uuid4(),
        incident_id=incident_id,
        evidence_type=EvidenceType.TELEMETRY_METRIC,
        source="stream",
        observed_at=datetime.now(timezone.utc),
        summary="Minor latency fluctuation",
    )

    result = await agent.investigate(
        incident_id=str(incident_id),
        merchant_id=str(merchant_id),
        incident_type="payment_drop_spike",
        severity="low",
        revenue_at_risk=Decimal("500.00"),
        currency="INR",
        description="Fluctuation",
        evidences=[evidence_item],
    )

    assert result.confidence == Decimal("0.25")
    assert result.is_conclusive is False
