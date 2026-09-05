"""Tests for LangGraph StateGraph workflow execution."""

from datetime import datetime, timezone
from decimal import Decimal
from uuid import uuid4
import pytest

from app.agents.graph.state import IncidentInvestigationState, WorkflowStatus
from app.agents.graph.workflow import create_incident_investigation_graph
from app.ai.gateway import AIGateway
from app.ai.providers.fake_provider import FakeProvider
from app.domain.actions.enums import ActionType
from app.domain.incidents.enums import IncidentSeverity, IncidentType
from app.infrastructure.evidence.deterministic_provider import DeterministicEvidenceProvider


@pytest.mark.anyio
async def test_langgraph_workflow_happy_path():
    """Verify complete end-to-end execution: START -> investigator -> recovery_planner -> END."""
    provider = FakeProvider()
    incident_id = uuid4()
    merchant_id = uuid4()

    # Step 1 response: Investigator, Step 2 response: Recovery Planner
    investigation_json = (
        f'{{"incident_id": "{str(incident_id)}", '
        f'"primary_cause": "HDFC netbanking upstream 504 gateway timeout", '
        f'"secondary_causes": [], '
        f'"confidence": 0.95, '
        f'"confidence_rationale": "Direct correlation with 504 logs.", '
        f'"affected_cohorts": ["HDFC_NETBANKING"], '
        f'"evidence_keys_used": ["ev_1"], '
        f'"is_conclusive": true}}'
    )
    planner_json = (
        '{"action_type": "gateway_reroute", '
        '"target": "gateway_axis_backup", '
        '"expected_recovery_ratio": 0.85, '
        '"risk_level": "low", '
        '"confidence": 0.90, '
        '"rationale": "Reroute HDFC netbanking to backup aggregator."}'
    )

    call_count = 0

    async def dynamic_generate_structured(*args, **kwargs):
        nonlocal call_count
        call_count += 1
        if call_count == 1:
            return investigation_json
        return planner_json

    provider.generate_structured_json = dynamic_generate_structured

    gateway = AIGateway(provider=provider, default_model="gpt-4o-mini")
    evidence_provider = DeterministicEvidenceProvider()
    graph = create_incident_investigation_graph(gateway=gateway, evidence_provider=evidence_provider)

    initial_state: IncidentInvestigationState = {
        "merchant_id": merchant_id,
        "incident_id": incident_id,
        "incident_type": IncidentType.PAYMENT_DROP_SPIKE,
        "severity": IncidentSeverity.HIGH,
        "detected_at": datetime.now(timezone.utc),
        "currency": "INR",
        "description": "Payment drop observed",
        "baseline_hourly_rate": Decimal("20000.00"),
        "current_hourly_rate": Decimal("8000.00"),
        "duration_hours": Decimal("2.0"),
        "revenue_at_risk": Decimal("0.00"),  # Will be calculated to 24000.00
        "status": WorkflowStatus.INITIALIZED,
    }

    final_state = await graph.ainvoke(initial_state)

    assert final_state["status"] == WorkflowStatus.COMPLETED
    assert final_state["revenue_at_risk"] == Decimal("24000.00")
    assert final_state["investigation"] is not None
    assert final_state["investigation"].primary_cause == "HDFC netbanking upstream 504 gateway timeout"
    assert final_state["proposed_action"] is not None
    assert final_state["proposed_action"].action_type == ActionType.GATEWAY_REROUTE
    # 24000.00 * 0.85 = 20400.00
    assert final_state["proposed_action"].expected_recovery == Decimal("20400.00")
    assert len(final_state["evidences"]) >= 2
