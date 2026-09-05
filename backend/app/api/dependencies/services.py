"""FastAPI dependency providers for application services."""

from typing import AsyncGenerator
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.ports.unit_of_work import UnitOfWork
from app.application.services.action_service import ActionService
from app.application.services.incident_service import IncidentService
from app.application.services.investigation_service import InvestigationService
from app.application.services.verification_service import VerificationService
from app.infrastructure.database.session import get_async_db
from app.infrastructure.database.unit_of_work import SQLAlchemyUnitOfWork


async def get_uow(session: AsyncSession = Depends(get_async_db)) -> AsyncGenerator[UnitOfWork, None]:
    """Dependency provider yielding a SQLAlchemyUnitOfWork."""
    yield SQLAlchemyUnitOfWork(session)


async def get_incident_service(uow: UnitOfWork = Depends(get_uow)) -> IncidentService:
    """Dependency provider for IncidentService."""
    return IncidentService(uow)


async def get_investigation_service(uow: UnitOfWork = Depends(get_uow)) -> InvestigationService:
    """Dependency provider for InvestigationService."""
    return InvestigationService(uow)


async def get_action_service(uow: UnitOfWork = Depends(get_uow)) -> ActionService:
    """Dependency provider for ActionService."""
    return ActionService(uow)


async def get_verification_service(uow: UnitOfWork = Depends(get_uow)) -> VerificationService:
    """Dependency provider for VerificationService."""
    return VerificationService(uow)
