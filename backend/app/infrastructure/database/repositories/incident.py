"""SQLAlchemy implementations of IncidentRepository and EvidenceRepository."""

from typing import List, Optional
from uuid import UUID
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.ports.repositories import EvidenceRepository, IncidentRepository
from app.domain.incidents.models import Evidence, Incident
from app.infrastructure.database.mappers import (
    evidence_to_orm,
    incident_to_orm,
    orm_to_evidence,
    orm_to_incident,
)
from app.infrastructure.database.models.incident import EvidenceORM, IncidentORM


class SQLAlchemyIncidentRepository(IncidentRepository):
    """SQLAlchemy Async implementation of IncidentRepository port."""

    def __init__(self, session: AsyncSession):
        self._session = session

    async def save(self, incident: Incident) -> Incident:
        """Persist or update an Incident entity."""
        stmt = select(IncidentORM).where(IncidentORM.incident_id == incident.incident_id)
        result = await self._session.execute(stmt)
        existing = result.scalar_one_or_none()

        if existing:
            existing.merchant_id = incident.merchant_id
            existing.incident_type = incident.incident_type.value
            existing.severity = incident.severity.value
            existing.status = incident.status.value
            existing.detected_at = incident.detected_at
            existing.revenue_at_risk = incident.revenue_at_risk
            existing.currency = incident.currency
            existing.confidence = incident.confidence
            existing.description = incident.description
            orm_instance = existing
        else:
            orm_instance = incident_to_orm(incident)
            self._session.add(orm_instance)

        await self._session.flush()
        return orm_to_incident(orm_instance)

    async def get_by_id(self, incident_id: UUID) -> Optional[Incident]:
        """Retrieve an Incident by its unique identifier."""
        stmt = select(IncidentORM).where(IncidentORM.incident_id == incident_id)
        result = await self._session.execute(stmt)
        orm = result.scalar_one_or_none()
        return orm_to_incident(orm) if orm else None

    async def list_by_merchant(self, merchant_id: UUID, limit: int = 50) -> List[Incident]:
        """Retrieve revenue incidents associated with a merchant."""
        stmt = (
            select(IncidentORM)
            .where(IncidentORM.merchant_id == merchant_id)
            .order_by(IncidentORM.detected_at.desc())
            .limit(limit)
        )
        result = await self._session.execute(stmt)
        return [orm_to_incident(row) for row in result.scalars().all()]


class SQLAlchemyEvidenceRepository(EvidenceRepository):
    """SQLAlchemy Async implementation of EvidenceRepository port."""

    def __init__(self, session: AsyncSession):
        self._session = session

    async def save(self, evidence: Evidence) -> Evidence:
        """Persist an Evidence item."""
        stmt = select(EvidenceORM).where(EvidenceORM.evidence_id == evidence.evidence_id)
        result = await self._session.execute(stmt)
        existing = result.scalar_one_or_none()

        if existing:
            existing.incident_id = evidence.incident_id
            existing.evidence_type = evidence.evidence_type.value
            existing.source = evidence.source
            existing.observed_at = evidence.observed_at
            existing.summary = evidence.summary
            existing.metrics_data_json = dict(evidence.metrics_data)
            orm_instance = existing
        else:
            orm_instance = evidence_to_orm(evidence)
            self._session.add(orm_instance)

        await self._session.flush()
        return orm_to_evidence(orm_instance)

    async def get_by_id(self, evidence_id: UUID) -> Optional[Evidence]:
        """Retrieve an Evidence item by its unique identifier."""
        stmt = select(EvidenceORM).where(EvidenceORM.evidence_id == evidence_id)
        result = await self._session.execute(stmt)
        orm = result.scalar_one_or_none()
        return orm_to_evidence(orm) if orm else None

    async def list_by_incident(self, incident_id: UUID) -> List[Evidence]:
        """Retrieve evidence items associated with an incident."""
        stmt = (
            select(EvidenceORM)
            .where(EvidenceORM.incident_id == incident_id)
            .order_by(EvidenceORM.observed_at.desc())
        )
        result = await self._session.execute(stmt)
        return [orm_to_evidence(row) for row in result.scalars().all()]
