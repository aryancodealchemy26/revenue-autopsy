"""Tests for AI provider failure resilience in LangGraph workflow."""

from datetime import datetime, timezone
from decimal import Decimal
from uuid import uuid4
import pytest

from app.agents.graph.state import IncidentInvestigationState, WorkflowStatus
from app.agents.graph.workflow import create_incident_investigation_graph
from app.ai.errors import AIRateLimitError
from app.ai.gateway import AIGateway
from app.ai.providers.fake_provider import FakeProvider
from app.domain.incidents.enums import IncidentSeverity, IncidentType
from app.infrastructure.evidence.deterministic_provider import DeterministicEvidenceProvider


@pytest.mark.anyio
async def test_workflow_ai_unavailable_resilience():
    """Verify workflow gracefully transitions to AI_UNAVAILABLE on transient AI failures."""
    provider = FakeProvider()
    incident_id = uuid4()
    merchant_id = uuid4()

    async def fail_generate(*args, **kwargs):
        raise AIRateLimitError("Provider 429 Rate Limit Exceeded")

    provider.generate_structured_json = fail_generate

    gateway = AIGateway(
        provider=provider,
        default_model="gpt-4o-mini",
        max_retries=1,
        backoff_factor=0.01,
    )
    evidence_provider = DeterministicEvidenceProvider()
    graph = create_incident_investigation_graph(gateway=gateway, evidence_provider=evidence_provider)

    initial_state: IncidentInvestigationState = {
        "merchant_id": merchant_id,
        "incident_id": incident_id,
        "incident_type": IncidentType.PAYMENT_DROP_SPIKE,
        "severity": IncidentSeverity.HIGH,
        "detected_at": datetime.now(timezone.utc),
        "currency": "INR",
        "description": "Payment drop",
        "revenue_at_risk": Decimal("5000.00"),
        "status": WorkflowStatus.INITIALIZED,
    }

    final_state = await graph.ainvoke(initial_state)

    assert final_state["status"] == WorkflowStatus.AI_UNAVAILABLE
    assert "AI Gateway unavailable" in final_state.get("error_message", "")
    assert final_state.get("proposed_action") is None


@pytest.mark.anyio
async def test_workflow_malformed_json_failure_resilience():
    """Verify workflow gracefully transitions to FAILED on unparseable JSON without crashing."""
    provider = FakeProvider()
    incident_id = uuid4()
    merchant_id = uuid4()

    provider.canned_json = "INVALID_NOT_JSON"

    gateway = AIGateway(provider=provider, default_model="gpt-4o-mini", max_retries=1, backoff_factor=0.01)
    evidence_provider = DeterministicEvidenceProvider()
    graph = create_incident_investigation_graph(gateway=gateway, evidence_provider=evidence_provider)

    initial_state: IncidentInvestigationState = {
        "merchant_id": merchant_id,
        "incident_id": incident_id,
        "incident_type": IncidentType.PAYMENT_DROP_SPIKE,
        "severity": IncidentSeverity.HIGH,
        "detected_at": datetime.now(timezone.utc),
        "currency": "INR",
        "description": "Payment drop",
        "revenue_at_risk": Decimal("5000.00"),
        "status": WorkflowStatus.INITIALIZED,
    }

    final_state = await graph.ainvoke(initial_state)

    assert final_state["status"] == WorkflowStatus.FAILED
    assert final_state.get("proposed_action") is None
