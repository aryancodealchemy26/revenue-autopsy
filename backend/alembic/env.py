import asyncio
import os
from logging.config import fileConfig
from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import async_engine_from_config
from alembic import context

from app.core.config import settings
from app.infrastructure.database.base import Base
# Import all ORM models to register metadata
import app.infrastructure.database.models  # noqa: F401

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata


def get_url():
    # 1. Check -x command line argument
    x_args = context.get_x_argument(as_dictionary=True)
    if "sqlalchemy.url" in x_args:
        return x_args["sqlalchemy.url"]
    # 2. Check environment variable
    if os.environ.get("DATABASE_URL"):
        return os.environ.get("DATABASE_URL")
    # 3. Check application settings
    if settings.DATABASE_URL and settings.DATABASE_URL.get_secret_value():
        return settings.DATABASE_URL.get_secret_value()
    # 4. Fallback to alembic.ini config option
    return config.get_main_option("sqlalchemy.url", "postgresql+asyncpg://postgres:postgres@localhost:5432/revenue_autopsy")


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode."""
    url = get_url()
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection: Connection) -> None:
    context.configure(connection=connection, target_metadata=target_metadata)

    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    """Run migrations in 'online' mode with async engine."""
    configuration = config.get_section(config.config_ini_section, {})
    configuration["sqlalchemy.url"] = get_url()

    connectable = async_engine_from_config(
        configuration,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)

    await connectable.dispose()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode."""
    asyncio.run(run_async_migrations())


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
