"""Async SQLAlchemy Engine and Session Management."""

from typing import AsyncGenerator, Optional
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.core.config import settings


def get_db_url() -> str:
    """Extract string database URL from settings SecretStr."""
    if settings.DATABASE_URL and settings.DATABASE_URL.get_secret_value():
        return settings.DATABASE_URL.get_secret_value()
    # Default placeholder url for unconfigured dev setup (asyncpg)
    return "postgresql+asyncpg://postgres:postgres@localhost:5432/revenue_autopsy"


def create_custom_async_engine(db_url: Optional[str] = None) -> AsyncEngine:
    """Create an AsyncEngine instance."""
    url = db_url or get_db_url()
    # Handle sqlite vs postgres engine kwargs
    if "sqlite" in url:
        return create_async_engine(url, echo=settings.DB_ECHO)
    return create_async_engine(
        url,
        echo=settings.DB_ECHO,
        pool_size=settings.DB_POOL_SIZE,
        max_overflow=settings.DB_MAX_OVERFLOW,
    )


async_engine: AsyncEngine = create_custom_async_engine()

AsyncSessionLocal = async_sessionmaker(
    bind=async_engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
)


async def get_async_db() -> AsyncGenerator[AsyncSession, None]:
    """Dependency generator yielding an AsyncSession."""
    async with AsyncSessionLocal() as session:
        yield session
