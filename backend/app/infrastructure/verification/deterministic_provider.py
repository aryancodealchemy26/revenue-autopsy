"""Deterministic Verification Evidence Provider for testing and local sandbox verification."""

from datetime import datetime, timezone
from decimal import Decimal
from typing import Any, Dict, List, Optional
from uuid import UUID, uuid4

from app.application.ports.verification_provider import VerificationEvidenceProviderPort
from app.domain.incidents.enums import EvidenceType
from app.domain.incidents.models import Evidence


class DeterministicVerificationEvidenceProvider(VerificationEvidenceProviderPort):
    """Deterministic evidence provider generating post-execution diagnostic telemetry for verification."""

    def __init__(self, override_metrics: Optional[Dict[str, Any]] = None):
        self._override_metrics = override_metrics

    async def get_post_execution_evidence(
        self,
        merchant_id: UUID,
        incident_id: UUID,
        action_id: UUID,
        executed_at: datetime,
        correlation_id: Optional[str] = None,
    ) -> List[Evidence]:
        """Generate deterministic post-execution telemetry."""
        now = datetime.now(timezone.utc)
        metrics = self._override_metrics if self._override_metrics is not None else {
            "post_execution_success_rate": 0.985,
            "post_execution_error_rate": 0.012,
            "traffic_recovery_ratio": 1.0,
            "gateway_status": "healthy",
            "recovered_transactions_count": 14,
        }

        evidence = Evidence(
            evidence_id=uuid4(),
            incident_id=incident_id,
            evidence_type=EvidenceType.TELEMETRY_METRIC,
            source="verification_telemetry_stream",
            observed_at=now,
            summary="Post-execution telemetry confirms route stabilization and payment success recovery.",
            metrics_data=metrics,
        )

        return [evidence]
