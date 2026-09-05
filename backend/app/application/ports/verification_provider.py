"""Verification Evidence Provider Port interface for post-execution verification telemetry."""

from abc import ABC, abstractmethod
from datetime import datetime
from typing import List, Optional
from uuid import UUID

from app.domain.incidents.models import Evidence


class VerificationEvidenceProviderPort(ABC):
    """Abstract Port for querying post-execution diagnostic telemetry to verify revenue recovery."""

    @abstractmethod
    async def get_post_execution_evidence(
        self,
        merchant_id: UUID,
        incident_id: UUID,
        action_id: UUID,
        executed_at: datetime,
        correlation_id: Optional[str] = None,
    ) -> List[Evidence]:
        """Fetch post-execution telemetry and evidence to verify recovery effectiveness."""
        pass
