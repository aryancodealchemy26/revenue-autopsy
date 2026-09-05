"""Unit tests for explicit bidirectional domain <-> ORM mappers."""

from datetime import datetime, timezone
from decimal import Decimal
from uuid import uuid4

from app.domain.actions.enums import ActionStatus, ActionType, RiskLevel
from app.domain.actions.models import ActionPlan
from app.domain.incidents.enums import EvidenceType, IncidentSeverity, IncidentStatus, IncidentType
from app.domain.incidents.models import Evidence, Incident
from app.domain.merchants.enums import MerchantStatus
from app.domain.merchants.models import Merchant
from app.domain.outcomes.enums import OutcomeStatus, OutcomeType
from app.domain.outcomes.models import Outcome
from app.domain.revenue.enums import RevenueEventType
from app.domain.revenue.models import RevenueEvent
from app.infrastructure.database.mappers import (
    action_plan_to_orm,
    evidence_to_orm,
    incident_to_orm,
    merchant_to_orm,
    orm_to_action_plan,
    orm_to_evidence,
    orm_to_incident,
    orm_to_merchant,
    orm_to_outcome,
    orm_to_revenue_event,
    outcome_to_orm,
    revenue_event_to_orm,
)


def test_merchant_mapper_roundtrip():
    """Verify bidirectional mapping for Merchant preserves all fields and types."""
    merchant = Merchant(
        merchant_id=uuid4(),
        name="Razorpay Merchant Alpha",
        currency="INR",
        timezone="Asia/Kolkata",
        status=MerchantStatus.ACTIVE,
    )
    orm = merchant_to_orm(merchant)
    reconstructed = orm_to_merchant(orm)

    assert reconstructed.merchant_id == merchant.merchant_id
    assert reconstructed.name == merchant.name
    assert reconstructed.currency == merchant.currency
    assert reconstructed.timezone == merchant.timezone
    assert reconstructed.status == merchant.status


def test_revenue_event_mapper_roundtrip():
    """Verify bidirectional mapping for RevenueEvent preserves Decimal and UTC timezone."""
    now = datetime.now(timezone.utc)
    event = RevenueEvent(
        event_id=uuid4(),
        merchant_id=uuid4(),
        event_type=RevenueEventType.PAYMENT_SUCCESS,
        source="razorpay_webhook",
        timestamp=now,
        amount=Decimal("4999.5000"),
        currency="INR",
        metadata={"order_id": "order_xyz", "attempts": 1},
    )
    orm = revenue_event_to_orm(event)
    reconstructed = orm_to_revenue_event(orm)

    assert reconstructed.event_id == event.event_id
    assert reconstructed.merchant_id == event.merchant_id
    assert reconstructed.event_type == event.event_type
    assert reconstructed.source == event.source
    assert reconstructed.timestamp == event.timestamp
    assert reconstructed.amount == Decimal("4999.5000")
    assert isinstance(reconstructed.amount, Decimal)
    assert reconstructed.metadata == {"order_id": "order_xyz", "attempts": 1}


def test_incident_mapper_roundtrip():
    """Verify bidirectional mapping for Incident preserves Decimal scale, confidence, and status."""
    now = datetime.now(timezone.utc)
    incident = Incident(
        incident_id=uuid4(),
        merchant_id=uuid4(),
        incident_type=IncidentType.AUTHORIZATION_FAILURE_SURGE,
        severity=IncidentSeverity.HIGH,
        status=IncidentStatus.INVESTIGATING,
        detected_at=now,
        revenue_at_risk=Decimal("150000.0000"),
        currency="INR",
        confidence=Decimal("0.9500"),
        description="Authorization failure rate surged above 15% threshold",
    )
    orm = incident_to_orm(incident)
    reconstructed = orm_to_incident(orm)

    assert reconstructed.incident_id == incident.incident_id
    assert reconstructed.merchant_id == incident.merchant_id
    assert reconstructed.incident_type == incident.incident_type
    assert reconstructed.severity == incident.severity
    assert reconstructed.status == incident.status
    assert reconstructed.detected_at == incident.detected_at
    assert reconstructed.revenue_at_risk == Decimal("150000.0000")
    assert reconstructed.confidence == Decimal("0.9500")
    assert reconstructed.description == incident.description


def test_evidence_mapper_roundtrip():
    """Verify bidirectional mapping for Evidence preserves metrics data."""
    now = datetime.now(timezone.utc)
    evidence = Evidence(
        evidence_id=uuid4(),
        incident_id=uuid4(),
        evidence_type=EvidenceType.TELEMETRY_METRIC,
        source="gateway_monitor",
        observed_at=now,
        summary="Spike in 504 Gateway Timeout responses",
        metrics_data={"error_code_504_count": 42},
    )
    orm = evidence_to_orm(evidence)
    reconstructed = orm_to_evidence(orm)

    assert reconstructed.evidence_id == evidence.evidence_id
    assert reconstructed.incident_id == evidence.incident_id
    assert reconstructed.evidence_type == evidence.evidence_type
    assert reconstructed.source == evidence.source
    assert reconstructed.summary == evidence.summary
    assert reconstructed.metrics_data == {"error_code_504_count": 42}


def test_action_plan_mapper_roundtrip():
    """Verify bidirectional mapping for ActionPlan preserves approval and expected recovery."""
    now = datetime.now(timezone.utc)
    plan = ActionPlan(
        action_id=uuid4(),
        incident_id=uuid4(),
        action_type=ActionType.GATEWAY_REROUTE,
        target="secondary_gateway_pool",
        expected_recovery=Decimal("120000.0000"),
        currency="INR",
        risk_level=RiskLevel.LOW,
        confidence=Decimal("0.9000"),
        approval_required=True,
        status=ActionStatus.PROPOSED,
        rationale="Switching traffic to secondary provider to mitigate latency",
        created_at=now,
    )
    orm = action_plan_to_orm(plan)
    reconstructed = orm_to_action_plan(orm)

    assert reconstructed.action_id == plan.action_id
    assert reconstructed.incident_id == plan.incident_id
    assert reconstructed.action_type == plan.action_type
    assert reconstructed.expected_recovery == Decimal("120000.0000")
    assert reconstructed.approval_required is True
    assert reconstructed.status == plan.status


def test_outcome_mapper_roundtrip():
    """Verify bidirectional mapping for Outcome preserves measured recovery."""
    now = datetime.now(timezone.utc)
    outcome = Outcome(
        outcome_id=uuid4(),
        incident_id=uuid4(),
        action_id=uuid4(),
        outcome_type=OutcomeType.REVENUE_RECOVERED,
        amount=Decimal("115000.7500"),
        currency="INR",
        status=OutcomeStatus.VERIFIED,
        measured_at=now,
        reference_data={"verified_tx_count": 87},
    )
    orm = outcome_to_orm(outcome)
    reconstructed = orm_to_outcome(orm)

    assert reconstructed.outcome_id == outcome.outcome_id
    assert reconstructed.incident_id == outcome.incident_id
    assert reconstructed.action_id == outcome.action_id
    assert reconstructed.outcome_type == outcome.outcome_type
    assert reconstructed.amount == Decimal("115000.7500")
    assert reconstructed.status == outcome.status
    assert reconstructed.reference_data == {"verified_tx_count": 87}
