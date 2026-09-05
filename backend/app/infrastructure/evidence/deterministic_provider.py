"""Deterministic Evidence Provider implementation for offline analysis and hermetic testing."""

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from uuid import UUID, uuid4

from app.application.ports.evidence_provider import EvidenceProvider
from app.domain.incidents.enums import EvidenceType, IncidentType
from app.domain.incidents.models import Evidence


class DeterministicEvidenceProvider(EvidenceProvider):
    """Deterministic, read-only diagnostic evidence provider.

    Generates structured, domain-grounded Evidence objects based on incident types
    and optional pre-configured fixture data for hermetic, repeatable testing.
    """

    def __init__(self, override_evidence: Optional[List[Evidence]] = None):
        self._override_evidence: Optional[List[Evidence]] = override_evidence

    def set_override_evidence(self, evidence_list: Optional[List[Evidence]]) -> None:
        """Set or clear explicit canned evidence for test assertions."""
        self._override_evidence = evidence_list

    async def get_incident_evidence(
        self,
        merchant_id: UUID,
        incident_id: UUID,
        incident_type: IncidentType,
        observed_after: Optional[datetime] = None,
    ) -> List[Evidence]:
        """Fetch read-only deterministic diagnostic evidence for an incident."""
        if self._override_evidence is not None:
            return self._override_evidence

        now = observed_after or datetime.now(timezone.utc)

        if incident_type == IncidentType.PAYMENT_DROP_SPIKE:
            return [
                Evidence(
                    evidence_id=uuid4(),
                    incident_id=incident_id,
                    evidence_type=EvidenceType.TELEMETRY_METRIC,
                    source="gateway_telemetry_stream",
                    observed_at=now,
                    summary="Gateway error rate surged to 48.5% on primary HDFC netbanking route.",
                    metrics_data={
                        "route": "hdfc_netbanking_v2",
                        "error_code": "GATEWAY_TIMEOUT_504",
                        "error_rate": 0.485,
                        "baseline_error_rate": 0.012,
                        "impacted_cohort": "HDFC_NETBANKING",
                    },
                ),
                Evidence(
                    evidence_id=uuid4(),
                    incident_id=incident_id,
                    evidence_type=EvidenceType.LOG_EXCERPT,
                    source="payment_core_logs",
                    observed_at=now,
                    summary="Upstream banking provider returned repeated HTTP 504 Gateway Time-out.",
                    metrics_data={
                        "upstream_status": 504,
                        "sample_trace_id": "trace_hdfc_504_99214",
                        "affected_gateway": "gateway_hdfc_primary",
                    },
                ),
            ]
        elif incident_type == IncidentType.AUTHORIZATION_FAILURE_SURGE:
            return [
                Evidence(
                    evidence_id=uuid4(),
                    incident_id=incident_id,
                    evidence_type=EvidenceType.STATISTICAL_ANOMALY,
                    source="card_network_monitor",
                    observed_at=now,
                    summary="Authorization failure surge detected on Visa recurring subscriptions.",
                    metrics_data={
                        "network": "VISA",
                        "decline_code": "ISSUER_UNAVAILABLE_05",
                        "failure_rate": 0.62,
                        "impacted_cohort": "CARDS_VISA_RECURRING",
                    },
                )
            ]
        elif incident_type == IncidentType.WEBHOOK_LATENCY_SPIKE:
            return [
                Evidence(
                    evidence_id=uuid4(),
                    incident_id=incident_id,
                    evidence_type=EvidenceType.API_TRACE,
                    source="webhook_dispatcher",
                    observed_at=now,
                    summary="Merchant webhook delivery p99 latency spiked to 18.2 seconds.",
                    metrics_data={
                        "p99_latency_ms": 18200,
                        "baseline_p99_ms": 320,
                        "timeout_rate": 0.35,
                        "endpoint": "/api/v1/razorpay/webhook",
                    },
                )
            ]
        else:
            return [
                Evidence(
                    evidence_id=uuid4(),
                    incident_id=incident_id,
                    evidence_type=EvidenceType.TELEMETRY_METRIC,
                    source="general_telemetry",
                    observed_at=now,
                    summary=f"Telemetry anomaly detected for incident type {incident_type.value}.",
                    metrics_data={"incident_type": incident_type.value},
                )
            ]

    async def get_metrics_snapshot(
        self,
        merchant_id: UUID,
        start_time: datetime,
        end_time: datetime,
    ) -> Dict[str, Any]:
        """Fetch aggregated telemetry snapshot metrics."""
        return {
            "merchant_id": str(merchant_id),
            "start_time": start_time.isoformat(),
            "end_time": end_time.isoformat(),
            "aggregate_success_rate": 0.74,
            "aggregate_error_rate": 0.26,
            "total_transactions_evaluated": 1540,
        }
