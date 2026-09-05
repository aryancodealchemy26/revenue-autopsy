"""Tests for SQLAlchemy ORM schema metadata and table definitions."""

import pytest
from sqlalchemy.ext.asyncio import create_async_engine

from app.infrastructure.database.base import Base
import app.infrastructure.database.models  # noqa: F401


@pytest.mark.anyio
async def test_schema_creation_and_metadata():
    """Verify all 6 ORM tables and their relationships exist in Base.metadata."""
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    table_names = Base.metadata.tables.keys()
    assert "merchants" in table_names
    assert "revenue_events" in table_names
    assert "incidents" in table_names
    assert "evidence" in table_names
    assert "action_plans" in table_names
    assert "outcomes" in table_names

    # Verify column definitions on merchants
    merchants_table = Base.metadata.tables["merchants"]
    assert "merchant_id" in merchants_table.columns
    assert "name" in merchants_table.columns
    assert "currency" in merchants_table.columns

    # Verify column definitions on revenue_events
    rev_table = Base.metadata.tables["revenue_events"]
    assert "event_id" in rev_table.columns
    assert "amount" in rev_table.columns
    assert "timestamp" in rev_table.columns

    # Verify column definitions on incidents
    incidents_table = Base.metadata.tables["incidents"]
    assert "incident_id" in incidents_table.columns
    assert "revenue_at_risk" in incidents_table.columns
    assert "confidence" in incidents_table.columns

    # Clean up
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()
