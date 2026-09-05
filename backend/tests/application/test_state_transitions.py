"""Tests for deterministic state machine transition validators."""

import pytest

from app.application.errors import InvalidStateTransitionError
from app.application.state_machines import (
    VALID_ACTION_TRANSITIONS,
    VALID_INCIDENT_TRANSITIONS,
    validate_action_transition,
    validate_incident_transition,
)
from app.domain.actions.enums import ActionStatus
from app.domain.incidents.enums import IncidentStatus


def test_valid_incident_transitions():
    """Verify all valid incident transitions pass without raising exceptions."""
    for current, allowed_targets in VALID_INCIDENT_TRANSITIONS.items():
        # Same state transition is a no-op
        validate_incident_transition(current, current)
        for target in allowed_targets:
            validate_incident_transition(current, target)


def test_invalid_incident_transitions():
    """Verify invalid incident transitions raise InvalidStateTransitionError."""
    # Cannot jump from DETECTED directly to ACTION_APPROVED
    with pytest.raises(InvalidStateTransitionError):
        validate_incident_transition(IncidentStatus.DETECTED, IncidentStatus.ACTION_APPROVED)

    # Cannot transition out of CLOSED
    with pytest.raises(InvalidStateTransitionError):
        validate_incident_transition(IncidentStatus.CLOSED, IncidentStatus.DETECTED)


def test_valid_action_transitions():
    """Verify all valid action plan transitions pass without raising exceptions."""
    for current, allowed_targets in VALID_ACTION_TRANSITIONS.items():
        validate_action_transition(current, current)
        for target in allowed_targets:
            validate_action_transition(current, target)


def test_invalid_action_transitions():
    """Verify invalid action plan transitions raise InvalidStateTransitionError."""
    # Cannot jump from PROPOSED directly to COMPLETED
    with pytest.raises(InvalidStateTransitionError):
        validate_action_transition(ActionStatus.PROPOSED, ActionStatus.COMPLETED)

    # Cannot transition out of COMPLETED
    with pytest.raises(InvalidStateTransitionError):
        validate_action_transition(ActionStatus.COMPLETED, ActionStatus.PROPOSED)
