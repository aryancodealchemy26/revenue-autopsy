"""Tests for insufficient evidence handling in LangGraph workflow."""

from datetime import datetime, timezone
from decimal import Decimal
from uuid import uuid4
import pytest

from app.agents.graph.state import IncidentInvestigationState, WorkflowStatus
from app.agents.graph.workflow import create_incident_investigation_graph
from app.ai.gateway import AIGateway
from app.ai.providers.fake_provider import FakeProvider
from app.domain.incidents.enums import IncidentSeverity, IncidentType
from app.infrastructure.evidence.deterministic_provider import DeterministicEvidenceProvider


@pytest.mark.anyio
async def test_workflow_insufficient_evidence_bypasses_planner():
    """Verify inconclusive investigation terminates in INSUFFICIENT_EVIDENCE and planner is NOT run."""
    provider = FakeProvider()
    incident_id = uuid4()
    merchant_id = uuid4()

    # Canned inconclusive investigation output
    provider.canned_json = (
        f'{{"incident_id": "{str(incident_id)}", '
        f'"primary_cause": "Unknown anomaly", '
        f'"secondary_causes": [], '
        f'"confidence": 0.20, '
        f'"confidence_rationale": "Conflicting metrics across gateway logs.", '
        f'"affected_cohorts": [], '
        f'"evidence_keys_used": [], '
        f'"is_conclusive": false}}'
    )

    gateway = AIGateway(provider=provider, default_model="gpt-4o-mini")
    evidence_provider = DeterministicEvidenceProvider()
    graph = create_incident_investigation_graph(gateway=gateway, evidence_provider=evidence_provider)

    initial_state: IncidentInvestigationState = {
        "merchant_id": merchant_id,
        "incident_id": incident_id,
        "incident_type": IncidentType.PAYMENT_DROP_SPIKE,
        "severity": IncidentSeverity.LOW,
        "detected_at": datetime.now(timezone.utc),
        "currency": "INR",
        "description": "Minor anomaly",
        "revenue_at_risk": Decimal("1000.00"),
        "status": WorkflowStatus.INITIALIZED,
    }

    final_state = await graph.ainvoke(initial_state)

    assert final_state["status"] == WorkflowStatus.INSUFFICIENT_EVIDENCE
    assert final_state["investigation"] is not None
    assert final_state["investigation"].is_conclusive is False
    # Planner MUST NOT have run
    assert final_state.get("proposed_action") is None
