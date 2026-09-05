"""Tests for DeterministicEvidenceProvider."""

from datetime import datetime, timezone
from uuid import uuid4
import pytest

from app.domain.incidents.enums import EvidenceType, IncidentType
from app.infrastructure.evidence.deterministic_provider import DeterministicEvidenceProvider


@pytest.mark.anyio
async def test_deterministic_evidence_payment_drop():
    """Verify evidence items generated for PAYMENT_DROP_SPIKE."""
    provider = DeterministicEvidenceProvider()
    merchant_id = uuid4()
    incident_id = uuid4()

    evidences = await provider.get_incident_evidence(
        merchant_id=merchant_id,
        incident_id=incident_id,
        incident_type=IncidentType.PAYMENT_DROP_SPIKE,
    )

    assert len(evidences) >= 2
    assert all(ev.incident_id == incident_id for ev in evidences)
    assert any(ev.evidence_type == EvidenceType.TELEMETRY_METRIC for ev in evidences)
    assert any(ev.evidence_type == EvidenceType.LOG_EXCERPT for ev in evidences)


@pytest.mark.anyio
async def test_deterministic_evidence_auth_failure():
    """Verify evidence items generated for AUTHORIZATION_FAILURE_SURGE."""
    provider = DeterministicEvidenceProvider()
    merchant_id = uuid4()
    incident_id = uuid4()

    evidences = await provider.get_incident_evidence(
        merchant_id=merchant_id,
        incident_id=incident_id,
        incident_type=IncidentType.AUTHORIZATION_FAILURE_SURGE,
    )

    assert len(evidences) >= 1
    assert evidences[0].evidence_type == EvidenceType.STATISTICAL_ANOMALY
    assert "CARDS_VISA_RECURRING" in evidences[0].metrics_data.get("impacted_cohort", "")


@pytest.mark.anyio
async def test_deterministic_metrics_snapshot():
    """Verify metrics snapshot aggregation."""
    provider = DeterministicEvidenceProvider()
    merchant_id = uuid4()
    start = datetime.now(timezone.utc)
    end = datetime.now(timezone.utc)

    metrics = await provider.get_metrics_snapshot(merchant_id, start, end)
    assert metrics["merchant_id"] == str(merchant_id)
    assert "aggregate_success_rate" in metrics
