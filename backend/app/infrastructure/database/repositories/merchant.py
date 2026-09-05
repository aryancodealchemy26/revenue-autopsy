"""SQLAlchemy implementation of MerchantRepository."""

from typing import Optional
from uuid import UUID
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.ports.repositories import MerchantRepository
from app.domain.merchants.models import Merchant
from app.infrastructure.database.mappers import merchant_to_orm, orm_to_merchant
from app.infrastructure.database.models.merchant import MerchantORM


class SQLAlchemyMerchantRepository(MerchantRepository):
    """SQLAlchemy Async implementation of MerchantRepository port."""

    def __init__(self, session: AsyncSession):
        self._session = session

    async def save(self, merchant: Merchant) -> Merchant:
        """Persist or update a Merchant entity."""
        stmt = select(MerchantORM).where(MerchantORM.merchant_id == merchant.merchant_id)
        result = await self._session.execute(stmt)
        existing = result.scalar_one_or_none()

        if existing:
            existing.name = merchant.name
            existing.currency = merchant.currency
            existing.timezone = merchant.timezone
            existing.status = merchant.status.value
            orm_instance = existing
        else:
            orm_instance = merchant_to_orm(merchant)
            self._session.add(orm_instance)

        await self._session.flush()
        return orm_to_merchant(orm_instance)

    async def get_by_id(self, merchant_id: UUID) -> Optional[Merchant]:
        """Retrieve a Merchant by its unique identifier."""
        stmt = select(MerchantORM).where(MerchantORM.merchant_id == merchant_id)
        result = await self._session.execute(stmt)
        orm = result.scalar_one_or_none()
        return orm_to_merchant(orm) if orm else None
