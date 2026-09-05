"""Tests for incident and evidence domain models."""

from datetime import datetime, timezone
from decimal import Decimal
from uuid import uuid4
import pytest
from pydantic import ValidationError

from app.domain.incidents.enums import (
    EvidenceType,
    IncidentSeverity,
    IncidentStatus,
    IncidentType,
)
from app.domain.incidents.models import Evidence, Incident


def test_evidence_creation_valid():
    """Test valid standalone Evidence creation linked by incident_id."""
    now = datetime.now(timezone.utc)
    incident_id = uuid4()
    evidence = Evidence(
        incident_id=incident_id,
        evidence_type=EvidenceType.TELEMETRY_METRIC,
        source="authorization_monitor",
        observed_at=now,
        summary="Authorization failure rate spiked from 1.2% to 18.5%",
        metrics_data={"failure_rate_percentage": 18.5},
    )
    assert evidence.incident_id == incident_id
    assert evidence.evidence_type == EvidenceType.TELEMETRY_METRIC


def test_incident_creation_valid():
    """Test valid Incident creation without embedded evidences list."""
    now = datetime.now(timezone.utc)
    merchant_id = uuid4()
    incident_id = uuid4()

    incident = Incident(
        incident_id=incident_id,
        merchant_id=merchant_id,
        incident_type=IncidentType.AUTHORIZATION_FAILURE_SURGE,
        severity=IncidentSeverity.CRITICAL,
        status=IncidentStatus.DETECTED,
        detected_at=now,
        revenue_at_risk=Decimal("125000.00"),
        currency="INR",
        confidence=Decimal("0.92"),
        description="High authorization failure spike observed across HDFC gateway node",
    )

    assert incident.incident_id == incident_id
    assert incident.confidence == Decimal("0.92")
    assert isinstance(incident.revenue_at_risk, Decimal)
    assert not hasattr(incident, "evidences")


def test_incident_float_inputs_rejection():
    """Test that float inputs for revenue_at_risk and confidence are rejected."""
    now = datetime.now(timezone.utc)
    merchant_id = uuid4()

    with pytest.raises(ValidationError, match="Float inputs are not allowed for monetary amounts"):
        Incident(
            merchant_id=merchant_id,
            incident_type=IncidentType.PAYMENT_DROP_SPIKE,
            severity=IncidentSeverity.HIGH,
            detected_at=now,
            revenue_at_risk=125000.00,  # float input
            confidence=Decimal("0.90"),
            description="Test float revenue_at_risk rejection",
        )

    with pytest.raises(ValidationError, match="Float inputs are not allowed for confidence scores"):
        Incident(
            merchant_id=merchant_id,
            incident_type=IncidentType.PAYMENT_DROP_SPIKE,
            severity=IncidentSeverity.HIGH,
            detected_at=now,
            revenue_at_risk=Decimal("125000.00"),
            confidence=0.90,  # float input
            description="Test float confidence rejection",
        )


def test_incident_invalid_confidence_rejection():
    """Test confidence out of range [0.00, 1.00] rejection."""
    now = datetime.now(timezone.utc)
    merchant_id = uuid4()

    with pytest.raises(ValidationError):
        Incident(
            merchant_id=merchant_id,
            incident_type=IncidentType.PAYMENT_DROP_SPIKE,
            severity=IncidentSeverity.HIGH,
            detected_at=now,
            revenue_at_risk=Decimal("5000.00"),
            confidence=Decimal("1.50"),  # Out of range (> 1.0)
            description="Test invalid confidence",
        )
