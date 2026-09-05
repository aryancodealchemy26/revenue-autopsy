"""PostgreSQL DDL compilation and Alembic migration schema verification tests."""

import importlib.util
from pathlib import Path
import pytest
from sqlalchemy.dialects import postgresql
from sqlalchemy.schema import CreateIndex, CreateTable

from app.infrastructure.database.base import Base
import app.infrastructure.database.models  # noqa: F401


def test_postgresql_ddl_compilation_all_tables():
    """Verify that all 6 ORM tables compile to valid PostgreSQL DDL with native types."""
    pg_dialect = postgresql.dialect()

    for table in Base.metadata.sorted_tables:
        ddl_str = str(CreateTable(table).compile(dialect=pg_dialect))
        assert table.name in ddl_str

        # Validate PostgreSQL native types compiled in DDL
        if table.name == "merchants":
            assert "UUID" in ddl_str or "uuid" in ddl_str.lower()
        elif table.name == "revenue_events":
            assert "NUMERIC(18, 4)" in ddl_str or "numeric(18, 4)" in ddl_str.lower()
            assert "JSONB" in ddl_str or "jsonb" in ddl_str.lower()
            assert "TIME ZONE" in ddl_str or "timestamptz" in ddl_str.lower()
        elif table.name == "incidents":
            assert "NUMERIC(18, 4)" in ddl_str
            assert "NUMERIC(5, 4)" in ddl_str
            assert "TIME ZONE" in ddl_str or "timestamptz" in ddl_str.lower()
        elif table.name == "action_plans":
            assert "BOOLEAN" in ddl_str or "boolean" in ddl_str.lower()
            assert "NUMERIC(18, 4)" in ddl_str
        elif table.name == "outcomes":
            assert "NUMERIC(18, 4)" in ddl_str
            assert "JSONB" in ddl_str or "jsonb" in ddl_str.lower()


def test_postgresql_ddl_compilation_all_indexes():
    """Verify that all indexes compile cleanly to valid PostgreSQL DDL."""
    pg_dialect = postgresql.dialect()

    for table in Base.metadata.sorted_tables:
        for idx in table.indexes:
            idx_ddl = str(CreateIndex(idx).compile(dialect=pg_dialect))
            assert idx.name in idx_ddl
            assert table.name in idx_ddl


def test_alembic_migration_functions_exist():
    """Verify that 001_initial_schema defines callable upgrade and downgrade functions."""
    migration_path = Path(__file__).parents[2] / "alembic" / "versions" / "001_initial_schema.py"
    assert migration_path.exists(), "001_initial_schema.py must exist in alembic/versions"

    spec = importlib.util.spec_from_file_location("initial_schema", migration_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    assert hasattr(module, "upgrade")
    assert callable(module.upgrade)
    assert hasattr(module, "downgrade")
    assert callable(module.downgrade)
    assert module.revision == "001_initial_schema"
