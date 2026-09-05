"""Tests for SQLAlchemyUnitOfWork implementation."""

from datetime import datetime, timezone
from decimal import Decimal
from uuid import uuid4
import pytest
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.domain.incidents.enums import IncidentSeverity, IncidentStatus, IncidentType
from app.domain.incidents.models import Incident
from app.domain.merchants.models import Merchant
from app.infrastructure.database.base import Base
from app.infrastructure.database.unit_of_work import SQLAlchemyUnitOfWork


@pytest.fixture
async def async_session():
    """Fixture providing isolated in-memory SQLite session."""
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
async def test_sqlalchemy_uow_commit(async_session: AsyncSession):
    """Verify SQLAlchemyUnitOfWork commits across multiple repositories atomically."""
    uow = SQLAlchemyUnitOfWork(async_session)

    merchant_id = uuid4()
    incident_id = uuid4()

    async with uow:
        await uow.merchants.save(
            Merchant(merchant_id=merchant_id, name="UoW Merchant", currency="INR")
        )
        await uow.incidents.save(
            Incident(
                incident_id=incident_id,
                merchant_id=merchant_id,
                incident_type=IncidentType.PAYMENT_DROP_SPIKE,
                severity=IncidentSeverity.HIGH,
                status=IncidentStatus.DETECTED,
                detected_at=datetime.now(timezone.utc),
                revenue_at_risk=Decimal("50000.0000"),
                confidence=Decimal("0.8500"),
                description="UoW test incident",
            )
        )
        await uow.commit()

    # Query directly in a new transaction context
    fetched_merchant = await uow.merchants.get_by_id(merchant_id)
    fetched_incident = await uow.incidents.get_by_id(incident_id)

    assert fetched_merchant is not None
    assert fetched_incident is not None


@pytest.mark.anyio
async def test_sqlalchemy_uow_automatic_rollback_on_exception(async_session: AsyncSession):
    """Verify SQLAlchemyUnitOfWork automatically rolls back on uncaught exception."""
    uow = SQLAlchemyUnitOfWork(async_session)
    merchant_id = uuid4()

    with pytest.raises(RuntimeError, match="Simulated application failure"):
        async with uow:
            await uow.merchants.save(
                Merchant(merchant_id=merchant_id, name="Failing Merchant", currency="INR")
            )
            raise RuntimeError("Simulated application failure")

    # Verify merchant was rolled back and is not in database
    fetched = await uow.merchants.get_by_id(merchant_id)
    assert fetched is None
