"""Evidence Provider port for incident diagnostic telemetry and evidence retrieval."""

from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID

from app.domain.incidents.enums import IncidentType
from app.domain.incidents.models import Evidence


class EvidenceProvider(ABC):
    """Abstract Port for retrieving diagnostic telemetry and evidence items.

    Implementations provide read-only diagnostic metrics for incidents
    without executing any mutations or financial writes.
    """

    @abstractmethod
    async def get_incident_evidence(
        self,
        merchant_id: UUID,
        incident_id: UUID,
        incident_type: IncidentType,
        observed_after: Optional[datetime] = None,
    ) -> List[Evidence]:
        """Fetch read-only deterministic diagnostic evidence items for an incident."""
        pass

    @abstractmethod
    async def get_metrics_snapshot(
        self,
        merchant_id: UUID,
        start_time: datetime,
        end_time: datetime,
    ) -> Dict[str, Any]:
        """Fetch aggregated telemetry metrics snapshot (e.g. failure rate, latency percentiles)."""
        pass
