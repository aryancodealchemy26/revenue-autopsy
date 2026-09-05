"""ActionPlan ORM model."""

from datetime import datetime
from decimal import Decimal
import uuid
from sqlalchemy import Boolean, DateTime, ForeignKey, Index, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.infrastructure.database.base import Base
from app.infrastructure.database.models.merchant import GUID


class ActionPlanORM(Base):
    """SQLAlchemy ORM model for action_plans table."""

    __tablename__ = "action_plans"

    action_id: Mapped[uuid.UUID] = mapped_column(GUID(), primary_key=True, default=uuid.uuid4)
    incident_id: Mapped[uuid.UUID] = mapped_column(GUID(), ForeignKey("incidents.incident_id", ondelete="CASCADE"), nullable=False)
    action_type: Mapped[str] = mapped_column(String(64), nullable=False)
    target: Mapped[str] = mapped_column(String(255), nullable=False)
    expected_recovery: Mapped[Decimal] = mapped_column(Numeric(18, 4), nullable=False)
    currency: Mapped[str] = mapped_column(String(3), nullable=False, default="INR")
    risk_level: Mapped[str] = mapped_column(String(32), nullable=False)
    confidence: Mapped[Decimal] = mapped_column(Numeric(5, 4), nullable=False)
    approval_required: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="proposed")
    rationale: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    # Relationships
    incident = relationship("IncidentORM", back_populates="action_plans")
    outcomes = relationship("OutcomeORM", back_populates="action_plan", cascade="all, delete-orphan")

    __table_args__ = (
        Index("idx_actions_incident_status", "incident_id", "status"),
    )
