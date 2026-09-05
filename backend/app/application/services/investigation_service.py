"""Investigation application service coordinating evidence and diagnostic context assembly."""

from typing import List
from uuid import UUID

from app.application.dtos.investigations import CreateEvidenceDTO, InvestigationContextDTO
from app.application.errors import IncidentNotFoundError, MerchantNotFoundError
from app.application.ports.unit_of_work import UnitOfWork
from app.domain.incidents.models import Evidence


class InvestigationService:
    """Application service for managing incident diagnostic evidence and assembling context."""

    def __init__(self, uow: UnitOfWork):
        self._uow = uow

    async def add_evidence(self, incident_id: UUID, dto: CreateEvidenceDTO) -> Evidence:
        """Attach an Evidence item to an existing Incident."""
        async with self._uow:
            # 1. Verify incident exists
            incident = await self._uow.incidents.get_by_id(incident_id)
            if not incident:
                raise IncidentNotFoundError(incident_id)

            # 2. Construct domain Evidence
            evidence = Evidence(
                evidence_id=dto.evidence_id,
                incident_id=incident_id,
                evidence_type=dto.evidence_type,
                source=dto.source,
                observed_at=dto.observed_at,
                summary=dto.summary,
                metrics_data=dto.metrics_data,
            )

            # 3. Persist and commit
            saved = await self._uow.evidence.save(evidence)
            await self._uow.commit()
            return saved

    async def get_incident_evidence(self, incident_id: UUID) -> List[Evidence]:
        """Retrieve all Evidence items attached to an Incident."""
        async with self._uow:
            incident = await self._uow.incidents.get_by_id(incident_id)
            if not incident:
                raise IncidentNotFoundError(incident_id)

            return await self._uow.evidence.list_by_incident(incident_id)

    async def assemble_investigation_context(self, incident_id: UUID) -> InvestigationContextDTO:
        """Assemble structured investigation context without calling AI or generating synthetic conclusions."""
        async with self._uow:
            # 1. Retrieve Incident
            incident = await self._uow.incidents.get_by_id(incident_id)
            if not incident:
                raise IncidentNotFoundError(incident_id)

            # 2. Retrieve Merchant
            merchant = await self._uow.merchants.get_by_id(incident.merchant_id)
            if not merchant:
                raise MerchantNotFoundError(incident.merchant_id)

            # 3. Retrieve Evidence
            evidences = await self._uow.evidence.list_by_incident(incident_id)

            # 4. Assemble context DTO
            return InvestigationContextDTO(
                incident=incident,
                merchant=merchant,
                evidences=evidences,
            )
