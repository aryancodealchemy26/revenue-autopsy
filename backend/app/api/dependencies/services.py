"""FastAPI dependency providers for application services."""

from typing import AsyncGenerator, Optional
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.gateway import AIGateway
from app.api.dependencies.ai import get_ai_gateway
from app.application.ports.evidence_provider import EvidenceProvider
from app.application.ports.policy_engine import PolicyEnginePort
from app.application.ports.unit_of_work import UnitOfWork
from app.application.services.action_service import ActionService
from app.application.services.incident_service import IncidentService
from app.application.services.investigation_service import InvestigationService
from app.application.services.orchestration_service import IncidentOrchestrationService
from app.application.services.verification_service import VerificationService
from app.execution.executor import ActionExecutor
from app.infrastructure.database.session import get_async_db
from app.infrastructure.database.unit_of_work import SQLAlchemyUnitOfWork
from app.infrastructure.evidence.deterministic_provider import DeterministicEvidenceProvider
from app.policies.engine import DeterministicPolicyEngine


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


def get_evidence_provider() -> EvidenceProvider:
    """Dependency provider for diagnostic EvidenceProvider."""
    return DeterministicEvidenceProvider()


def get_policy_engine() -> PolicyEnginePort:
    """Dependency provider for PolicyEngine."""
    return DeterministicPolicyEngine()


async def get_orchestration_service(
    uow: UnitOfWork = Depends(get_uow),
    gateway: AIGateway = Depends(get_ai_gateway),
    evidence_provider: EvidenceProvider = Depends(get_evidence_provider),
    policy_engine: PolicyEnginePort = Depends(get_policy_engine),
) -> IncidentOrchestrationService:
    """Dependency provider for IncidentOrchestrationService."""
    return IncidentOrchestrationService(
        uow=uow,
        gateway=gateway,
        evidence_provider=evidence_provider,
        policy_engine=policy_engine,
    )


async def get_executor(uow: UnitOfWork = Depends(get_uow)) -> ActionExecutor:
    """Dependency provider for ActionExecutor."""
    return ActionExecutor(uow=uow)
