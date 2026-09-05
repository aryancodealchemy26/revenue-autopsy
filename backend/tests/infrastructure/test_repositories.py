"""Tests for concrete async SQLAlchemy repository implementations."""

from datetime import datetime, timezone
from decimal import Decimal
from uuid import uuid4
import pytest
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.domain.actions.enums import ActionStatus, ActionType, RiskLevel
from app.domain.actions.models import ActionPlan
from app.domain.incidents.enums import EvidenceType, IncidentSeverity, IncidentStatus, IncidentType
from app.domain.incidents.models import Evidence, Incident
from app.domain.merchants.enums import MerchantStatus
from app.domain.merchants.models import Merchant
from app.domain.outcomes.enums import OutcomeStatus, OutcomeType
from app.domain.outcomes.models import Outcome
from app.domain.revenue.enums import RevenueEventType
from app.domain.revenue.models import RevenueEvent
from app.infrastructure.database.base import Base
from app.infrastructure.database.repositories.action import SQLAlchemyActionPlanRepository
from app.infrastructure.database.repositories.incident import (
    SQLAlchemyEvidenceRepository,
    SQLAlchemyIncidentRepository,
)
from app.infrastructure.database.repositories.merchant import SQLAlchemyMerchantRepository
from app.infrastructure.database.repositories.outcome import SQLAlchemyOutcomeRepository
from app.infrastructure.database.repositories.revenue import SQLAlchemyRevenueEventRepository


@pytest.fixture
async def async_session():
    """Fixture providing an isolated in-memory async SQLite session with all tables created."""
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    session_factory = async_sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)
    async with session_factory() as session:
        yield session

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()


@pytest.mark.anyio
async def test_merchant_repository_crud(async_session: AsyncSession):
    """Test save, update, and get_by_id in MerchantRepository."""
    repo = SQLAlchemyMerchantRepository(async_session)
    merchant_id = uuid4()
    merchant = Merchant(
        merchant_id=merchant_id,
        name="Merchant One",
        currency="INR",
        timezone="Asia/Kolkata",
        status=MerchantStatus.ACTIVE,
    )

    # 1. Save
    saved = await repo.save(merchant)
    assert saved.merchant_id == merchant_id
    assert saved.name == "Merchant One"

    # 2. Get by ID
    fetched = await repo.get_by_id(merchant_id)
    assert fetched is not None
    assert fetched.merchant_id == merchant_id
    assert fetched.status == MerchantStatus.ACTIVE

    # 3. Update
    updated_merchant = Merchant(
        merchant_id=merchant_id,
        name="Merchant One Updated",
        currency="INR",
        timezone="Asia/Kolkata",
        status=MerchantStatus.SUSPENDED,
    )
    saved_updated = await repo.save(updated_merchant)
    assert saved_updated.name == "Merchant One Updated"
    assert saved_updated.status == MerchantStatus.SUSPENDED


@pytest.mark.anyio
async def test_revenue_event_repository(async_session: AsyncSession):
    """Test save, get_by_id, and list_by_merchant in RevenueEventRepository."""
    merchant_repo = SQLAlchemyMerchantRepository(async_session)
    rev_repo = SQLAlchemyRevenueEventRepository(async_session)

    merchant = Merchant(merchant_id=uuid4(), name="Rev Merchant", currency="INR")
    await merchant_repo.save(merchant)

    now = datetime.now(timezone.utc)
    event1 = RevenueEvent(
        event_id=uuid4(),
        merchant_id=merchant.merchant_id,
        event_type=RevenueEventType.PAYMENT_SUCCESS,
        source="razorpay_webhook",
        timestamp=now,
        amount=Decimal("1999.0000"),
        currency="INR",
    )
    event2 = RevenueEvent(
        event_id=uuid4(),
        merchant_id=merchant.merchant_id,
        event_type=RevenueEventType.PAYMENT_FAILED,
        source="gateway_log",
        timestamp=now,
        amount=Decimal("500.0000"),
        currency="INR",
    )

    await rev_repo.save(event1)
    await rev_repo.save(event2)

    # Query by ID
    fetched = await rev_repo.get_by_id(event1.event_id)
    assert fetched is not None
    assert fetched.amount == Decimal("1999.0000")

    # List by merchant
    events = await rev_repo.list_by_merchant(merchant.merchant_id)
    assert len(events) == 2


@pytest.mark.anyio
async def test_incident_and_evidence_repositories(async_session: AsyncSession):
    """Test IncidentRepository and EvidenceRepository operations."""
    merchant_repo = SQLAlchemyMerchantRepository(async_session)
    incident_repo = SQLAlchemyIncidentRepository(async_session)
    evidence_repo = SQLAlchemyEvidenceRepository(async_session)

    merchant = Merchant(merchant_id=uuid4(), name="Inc Merchant", currency="INR")
    await merchant_repo.save(merchant)

    now = datetime.now(timezone.utc)
    incident = Incident(
        incident_id=uuid4(),
        merchant_id=merchant.merchant_id,
        incident_type=IncidentType.PAYMENT_DROP_SPIKE,
        severity=IncidentSeverity.CRITICAL,
        status=IncidentStatus.DETECTED,
        detected_at=now,
        revenue_at_risk=Decimal("75000.0000"),
        confidence=Decimal("0.9200"),
        description="Payment drop spike detected",
    )
    await incident_repo.save(incident)

    evidence = Evidence(
        evidence_id=uuid4(),
        incident_id=incident.incident_id,
        evidence_type=EvidenceType.LOG_EXCERPT,
        source="payment_gateway",
        observed_at=now,
        summary="Server error 500 spike",
    )
    await evidence_repo.save(evidence)

    # Verify retrieval
    inc_fetched = await incident_repo.get_by_id(incident.incident_id)
    assert inc_fetched is not None
    assert inc_fetched.revenue_at_risk == Decimal("75000.0000")

    ev_list = await evidence_repo.list_by_incident(incident.incident_id)
    assert len(ev_list) == 1
    assert ev_list[0].evidence_id == evidence.evidence_id


@pytest.mark.anyio
async def test_action_and_outcome_repositories(async_session: AsyncSession):
    """Test ActionPlanRepository and OutcomeRepository operations."""
    merchant_repo = SQLAlchemyMerchantRepository(async_session)
    incident_repo = SQLAlchemyIncidentRepository(async_session)
    action_repo = SQLAlchemyActionPlanRepository(async_session)
    outcome_repo = SQLAlchemyOutcomeRepository(async_session)

    merchant = Merchant(merchant_id=uuid4(), name="Act Merchant", currency="INR")
    await merchant_repo.save(merchant)

    now = datetime.now(timezone.utc)
    incident = Incident(
        incident_id=uuid4(),
        merchant_id=merchant.merchant_id,
        incident_type=IncidentType.AUTHORIZATION_FAILURE_SURGE,
        severity=IncidentSeverity.HIGH,
        detected_at=now,
        revenue_at_risk=Decimal("50000.0000"),
        confidence=Decimal("0.8500"),
        description="Auth failure spike",
    )
    await incident_repo.save(incident)

    plan = ActionPlan(
        action_id=uuid4(),
        incident_id=incident.incident_id,
        action_type=ActionType.GATEWAY_REROUTE,
        target="gateway_backup",
        expected_recovery=Decimal("45000.0000"),
        risk_level=RiskLevel.LOW,
        confidence=Decimal("0.8800"),
        rationale="Reroute to backup pool",
        created_at=now,
    )
    await action_repo.save(plan)

    outcome = Outcome(
        outcome_id=uuid4(),
        incident_id=incident.incident_id,
        action_id=plan.action_id,
        outcome_type=OutcomeType.REVENUE_RECOVERED,
        amount=Decimal("44200.0000"),
        measured_at=now,
    )
    await outcome_repo.save(outcome)

    fetched_outcome = await outcome_repo.get_by_action_id(plan.action_id)
    assert fetched_outcome is not None
    assert fetched_outcome.amount == Decimal("44200.0000")


@pytest.mark.anyio
async def test_transaction_rollback_behavior(async_session: AsyncSession):
    """Verify session.rollback() discards uncommitted repository operations."""
    repo = SQLAlchemyMerchantRepository(async_session)
    merchant = Merchant(merchant_id=uuid4(), name="Rollback Merchant", currency="INR")

    # Add entity via repository (which calls session.flush())
    await repo.save(merchant)

    # Roll back the transaction
    await async_session.rollback()

    # Verify entity does not persist after rollback
    fetched = await repo.get_by_id(merchant.merchant_id)
    assert fetched is None
