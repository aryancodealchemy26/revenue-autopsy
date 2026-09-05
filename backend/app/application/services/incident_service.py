"""Incident application service coordinating incident use cases."""

from typing import List
from uuid import UUID

from app.application.dtos.incidents import CreateIncidentDTO
from app.application.errors import IncidentNotFoundError, MerchantNotFoundError
from app.application.ports.unit_of_work import UnitOfWork
from app.application.state_machines import validate_incident_transition
from app.domain.incidents.enums import IncidentStatus
from app.domain.incidents.models import Incident


class IncidentService:
    """Application service for Incident creation, retrieval, listing, and state management."""

    def __init__(self, uow: UnitOfWork):
        self._uow = uow

    async def create_incident(self, dto: CreateIncidentDTO) -> Incident:
        """Create and persist a new Incident entity."""
        async with self._uow:
            # 1. Verify merchant exists
            merchant = await self._uow.merchants.get_by_id(dto.merchant_id)
            if not merchant:
                raise MerchantNotFoundError(dto.merchant_id)

            # 2. Construct domain entity
            incident = Incident(
                incident_id=dto.incident_id,
                merchant_id=dto.merchant_id,
                incident_type=dto.incident_type,
                severity=dto.severity,
                status=dto.status,
                detected_at=dto.detected_at,
                revenue_at_risk=dto.revenue_at_risk,
                currency=dto.currency,
                confidence=dto.confidence,
                description=dto.description,
            )

            # 3. Persist and commit
            saved = await self._uow.incidents.save(incident)
            await self._uow.commit()
            return saved

    async def get_incident(self, incident_id: UUID) -> Incident:
        """Retrieve an Incident by ID."""
        async with self._uow:
            incident = await self._uow.incidents.get_by_id(incident_id)
            if not incident:
                raise IncidentNotFoundError(incident_id)
            return incident

    async def update_incident_status(self, incident_id: UUID, new_status: IncidentStatus) -> Incident:
        """Update an Incident's status enforcing valid lifecycle transitions."""
        async with self._uow:
            incident = await self._uow.incidents.get_by_id(incident_id)
            if not incident:
                raise IncidentNotFoundError(incident_id)

            # Validate state transition
            validate_incident_transition(incident.status, new_status)

            # Update status
            incident.status = new_status
            saved = await self._uow.incidents.save(incident)
            await self._uow.commit()
            return saved

    async def list_merchant_incidents(self, merchant_id: UUID, limit: int = 50) -> List[Incident]:
        """List all incidents associated with a specific merchant."""
        async with self._uow:
            merchant = await self._uow.merchants.get_by_id(merchant_id)
            if not merchant:
                raise MerchantNotFoundError(merchant_id)

            return await self._uow.incidents.list_by_merchant(merchant_id, limit=limit)
