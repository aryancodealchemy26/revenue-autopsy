"""RevenueEvent ORM model."""

from datetime import datetime
from decimal import Decimal
from typing import Any, Dict
import uuid
from sqlalchemy import DateTime, ForeignKey, Index, Numeric, String, JSON
from sqlalchemy.dialects.postgresql import JSONB as PG_JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import TypeDecorator

from app.infrastructure.database.base import Base
from app.infrastructure.database.models.merchant import GUID


class JSONType(TypeDecorator):
    """Platform-independent JSON type. Uses PostgreSQL JSONB, fallback to JSON."""

    impl = JSON
    cache_ok = True

    def load_dialect_impl(self, dialect):
        if dialect.name == "postgresql":
            return dialect.type_descriptor(PG_JSONB())
        return dialect.type_descriptor(JSON())


class RevenueEventORM(Base):
    """SQLAlchemy ORM model for revenue_events table."""

    __tablename__ = "revenue_events"

    event_id: Mapped[uuid.UUID] = mapped_column(GUID(), primary_key=True, default=uuid.uuid4)
    merchant_id: Mapped[uuid.UUID] = mapped_column(GUID(), ForeignKey("merchants.merchant_id", ondelete="CASCADE"), nullable=False)
    event_type: Mapped[str] = mapped_column(String(64), nullable=False)
    source: Mapped[str] = mapped_column(String(255), nullable=False)
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    amount: Mapped[Decimal] = mapped_column(Numeric(18, 4), nullable=False)
    currency: Mapped[str] = mapped_column(String(3), nullable=False, default="INR")
    metadata_json: Mapped[Dict[str, Any]] = mapped_column(JSONType(), nullable=False, default=dict)

    # Relationship
    merchant = relationship("MerchantORM", back_populates="revenue_events")

    __table_args__ = (
        Index("idx_revenue_events_merchant_ts", "merchant_id", "timestamp"),
        Index("idx_revenue_events_type", "event_type"),
    )
