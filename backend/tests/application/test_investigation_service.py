"""Tests for InvestigationService application logic."""

from datetime import datetime, timezone
from decimal import Decimal
from uuid import uuid4
import pytest

from app.application.dtos.incidents import CreateIncidentDTO
from app.application.dtos.investigations import CreateEvidenceDTO
from app.application.errors import IncidentNotFoundError
from app.application.services.incident_service import IncidentService
from app.application.services.investigation_service import InvestigationService
from app.domain.incidents.enums import EvidenceType, IncidentSeverity, IncidentType
from app.domain.merchants.models import Merchant
from tests.application.fakes import FakeUnitOfWork


@pytest.mark.anyio
async def test_add_and_get_evidence():
    """Verify adding evidence to an incident and querying evidence list."""
    uow = FakeUnitOfWork()
    incident_service = IncidentService(uow)
    investigation_service = InvestigationService(uow)

    merchant = Merchant(merchant_id=uuid4(), name="Invest Merchant", currency="INR")
    await uow.merchants.save(merchant)

    incident = await incident_service.create_incident(
        CreateIncidentDTO(
            merchant_id=merchant.merchant_id,
            incident_type=IncidentType.AUTHORIZATION_FAILURE_SURGE,
            severity=IncidentSeverity.HIGH,
            detected_at=datetime.now(timezone.utc),
            revenue_at_risk=Decimal("60000.0000"),
            confidence=Decimal("0.8500"),
            description="Auth failure spike",
        )
    )

    ev_dto = CreateEvidenceDTO(
        evidence_type=EvidenceType.TELEMETRY_METRIC,
        source="gateway_log_parser",
        observed_at=datetime.now(timezone.utc),
        summary="502 Bad Gateway error spike observed",
        metrics_data={"error_code": 502, "error_rate": 0.18},
    )

    evidence = await investigation_service.add_evidence(incident.incident_id, ev_dto)
    assert evidence.incident_id == incident.incident_id
    assert evidence.evidence_type == EvidenceType.TELEMETRY_METRIC

    ev_list = await investigation_service.get_incident_evidence(incident.incident_id)
    assert len(ev_list) == 1
    assert ev_list[0].evidence_id == evidence.evidence_id


@pytest.mark.anyio
async def test_assemble_investigation_context():
    """Verify assembling structured investigation context without AI or external calls."""
    uow = FakeUnitOfWork()
    incident_service = IncidentService(uow)
    investigation_service = InvestigationService(uow)

    merchant = Merchant(merchant_id=uuid4(), name="Context Merchant", currency="INR")
    await uow.merchants.save(merchant)

    incident = await incident_service.create_incident(
        CreateIncidentDTO(
            merchant_id=merchant.merchant_id,
            incident_type=IncidentType.PAYMENT_DROP_SPIKE,
            severity=IncidentSeverity.CRITICAL,
            detected_at=datetime.now(timezone.utc),
            revenue_at_risk=Decimal("95000.0000"),
            confidence=Decimal("0.9200"),
            description="Payment drop across all nodes",
        )
    )

    await investigation_service.add_evidence(
        incident.incident_id,
        CreateEvidenceDTO(
            evidence_type=EvidenceType.LOG_EXCERPT,
            source="payment_gateway",
            observed_at=datetime.now(timezone.utc),
            summary="Network timeout contacting bank switch",
        ),
    )

    context_dto = await investigation_service.assemble_investigation_context(incident.incident_id)

    assert context_dto.incident.incident_id == incident.incident_id
    assert context_dto.merchant.merchant_id == merchant.merchant_id
    assert len(context_dto.evidences) == 1
    assert context_dto.evidences[0].summary == "Network timeout contacting bank switch"


@pytest.mark.anyio
async def test_investigation_service_missing_incident():
    """Verify missing incident raises IncidentNotFoundError in investigation service."""
    uow = FakeUnitOfWork()
    investigation_service = InvestigationService(uow)

    with pytest.raises(IncidentNotFoundError):
        await investigation_service.get_incident_evidence(uuid4())

    with pytest.raises(IncidentNotFoundError):
        await investigation_service.assemble_investigation_context(uuid4())
