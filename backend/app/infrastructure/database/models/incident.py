"""Incident and Evidence ORM models."""

from datetime import datetime
from decimal import Decimal
from typing import Any, Dict
import uuid
from sqlalchemy import DateTime, ForeignKey, Index, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.infrastructure.database.base import Base
from app.infrastructure.database.models.merchant import GUID
from app.infrastructure.database.models.revenue import JSONType


class IncidentORM(Base):
    """SQLAlchemy ORM model for incidents table."""

    __tablename__ = "incidents"

    incident_id: Mapped[uuid.UUID] = mapped_column(GUID(), primary_key=True, default=uuid.uuid4)
    merchant_id: Mapped[uuid.UUID] = mapped_column(GUID(), ForeignKey("merchants.merchant_id", ondelete="CASCADE"), nullable=False)
    incident_type: Mapped[str] = mapped_column(String(64), nullable=False)
    severity: Mapped[str] = mapped_column(String(32), nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="detected")
    detected_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    revenue_at_risk: Mapped[Decimal] = mapped_column(Numeric(18, 4), nullable=False)
    currency: Mapped[str] = mapped_column(String(3), nullable=False, default="INR")
    confidence: Mapped[Decimal] = mapped_column(Numeric(5, 4), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)

    # Relationships
    merchant = relationship("MerchantORM", back_populates="incidents")
    evidences = relationship("EvidenceORM", back_populates="incident", cascade="all, delete-orphan")
    action_plans = relationship("ActionPlanORM", back_populates="incident", cascade="all, delete-orphan")
    outcomes = relationship("OutcomeORM", back_populates="incident", cascade="all, delete-orphan")

    __table_args__ = (
        Index("idx_incidents_merchant_status", "merchant_id", "status"),
    )


class EvidenceORM(Base):
    """SQLAlchemy ORM model for evidence table."""

    __tablename__ = "evidence"

    evidence_id: Mapped[uuid.UUID] = mapped_column(GUID(), primary_key=True, default=uuid.uuid4)
    incident_id: Mapped[uuid.UUID] = mapped_column(GUID(), ForeignKey("incidents.incident_id", ondelete="CASCADE"), nullable=False)
    evidence_type: Mapped[str] = mapped_column(String(64), nullable=False)
    source: Mapped[str] = mapped_column(String(255), nullable=False)
    observed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    summary: Mapped[str] = mapped_column(Text, nullable=False)
    metrics_data_json: Mapped[Dict[str, Any]] = mapped_column(JSONType(), nullable=False, default=dict)

    # Relationship
    incident = relationship("IncidentORM", back_populates="evidences")

    __table_args__ = (
        Index("idx_evidence_incident_obs", "incident_id", "observed_at"),
    )
