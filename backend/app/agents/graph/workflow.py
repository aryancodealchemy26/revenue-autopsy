"""Compiled LangGraph workflow for Revenue Incident Investigation and Recovery Planning."""

from typing import Optional

from langgraph.graph import END, START, StateGraph

from app.agents.graph.nodes import IncidentWorkflowNodes, route_after_investigation
from app.agents.graph.state import IncidentInvestigationState
from app.agents.investigator.agent import InvestigatorAgent
from app.agents.planner.agent import RecoveryPlannerAgent
from app.ai.gateway import AIGateway
from app.application.ports.evidence_provider import EvidenceProvider


def create_incident_investigation_graph(
    gateway: AIGateway,
    evidence_provider: Optional[EvidenceProvider] = None,
    model: Optional[str] = None,
):
    """Build and compile the LangGraph incident response state machine.

    Topology:
        START -> investigator -> (route_after_investigation)
                                  ├── conclusive -> recovery_planner -> END
                                  └── inconclusive/failed -> END
    """
    investigator = InvestigatorAgent(gateway=gateway, model=model)
    planner = RecoveryPlannerAgent(gateway=gateway, model=model)
    workflow_nodes = IncidentWorkflowNodes(
        investigator=investigator,
        planner=planner,
        evidence_provider=evidence_provider,
    )

    builder = StateGraph(IncidentInvestigationState)

    # 1. Register processing nodes
    builder.add_node("investigator", workflow_nodes.investigator_node)
    builder.add_node("recovery_planner", workflow_nodes.recovery_planner_node)

    # 2. Wire entry point and conditional routing
    builder.add_edge(START, "investigator")
    builder.add_conditional_edges(
        "investigator",
        route_after_investigation,
        {
            "recovery_planner": "recovery_planner",
            "end": END,
        },
    )
    builder.add_edge("recovery_planner", END)

    # 3. Compile and return executable workflow graph
    return builder.compile()
