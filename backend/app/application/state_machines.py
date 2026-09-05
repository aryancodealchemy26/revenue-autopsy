"""Deterministic state machine transition validators for Incident and Action lifecycles."""

from typing import Dict, Set

from app.application.errors import InvalidStateTransitionError
from app.domain.actions.enums import ActionStatus
from app.domain.incidents.enums import IncidentStatus

# Valid transition graphs
VALID_INCIDENT_TRANSITIONS: Dict[IncidentStatus, Set[IncidentStatus]] = {
    IncidentStatus.DETECTED: {IncidentStatus.INVESTIGATING, IncidentStatus.CLOSED},
    IncidentStatus.INVESTIGATING: {IncidentStatus.ACTION_PROPOSED, IncidentStatus.CLOSED},
    IncidentStatus.ACTION_PROPOSED: {IncidentStatus.ACTION_APPROVED, IncidentStatus.CLOSED},
    IncidentStatus.ACTION_APPROVED: {IncidentStatus.RESOLVED, IncidentStatus.CLOSED},
    IncidentStatus.RESOLVED: {IncidentStatus.CLOSED},
    IncidentStatus.CLOSED: set(),
}

VALID_ACTION_TRANSITIONS: Dict[ActionStatus, Set[ActionStatus]] = {
    ActionStatus.PROPOSED: {ActionStatus.POLICY_CHECK_PENDING, ActionStatus.REJECTED},
    ActionStatus.POLICY_CHECK_PENDING: {ActionStatus.APPROVED, ActionStatus.REJECTED},
    ActionStatus.APPROVED: {ActionStatus.EXECUTING, ActionStatus.REJECTED},
    ActionStatus.EXECUTING: {ActionStatus.COMPLETED, ActionStatus.FAILED},
    ActionStatus.COMPLETED: set(),
    ActionStatus.FAILED: set(),
    ActionStatus.REJECTED: set(),
}


def validate_incident_transition(current_status: IncidentStatus, target_status: IncidentStatus) -> None:
    """Validate that an Incident status transition is allowed."""
    if current_status == target_status:
        return
    allowed_next = VALID_INCIDENT_TRANSITIONS.get(current_status, set())
    if target_status not in allowed_next:
        raise InvalidStateTransitionError("Incident", current_status.value, target_status.value)


def validate_action_transition(current_status: ActionStatus, target_status: ActionStatus) -> None:
    """Validate that an ActionPlan status transition is allowed."""
    if current_status == target_status:
        return
    allowed_next = VALID_ACTION_TRANSITIONS.get(current_status, set())
    if target_status not in allowed_next:
        raise InvalidStateTransitionError("ActionPlan", current_status.value, target_status.value)
