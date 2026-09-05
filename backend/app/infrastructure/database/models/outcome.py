"""Outcome ORM model."""

from datetime import datetime
from decimal import Decimal
from typing import Any, Dict
import uuid
from sqlalchemy import DateTime, ForeignKey, Index, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.infrastructure.database.base import Base
from app.infrastructure.database.models.merchant import GUID
from app.infrastructure.database.models.revenue import JSONType


class OutcomeORM(Base):
    """SQLAlchemy ORM model for outcomes table."""

    __tablename__ = "outcomes"

    outcome_id: Mapped[uuid.UUID] = mapped_column(GUID(), primary_key=True, default=uuid.uuid4)
    incident_id: Mapped[uuid.UUID] = mapped_column(GUID(), ForeignKey("incidents.incident_id", ondelete="CASCADE"), nullable=False)
    action_id: Mapped[uuid.UUID] = mapped_column(GUID(), ForeignKey("action_plans.action_id", ondelete="CASCADE"), nullable=False)
    outcome_type: Mapped[str] = mapped_column(String(64), nullable=False)
    amount: Mapped[Decimal] = mapped_column(Numeric(18, 4), nullable=False)
    currency: Mapped[str] = mapped_column(String(3), nullable=False, default="INR")
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="measured")
    measured_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    reference_data_json: Mapped[Dict[str, Any]] = mapped_column(JSONType(), nullable=False, default=dict)

    # Relationships
    incident = relationship("IncidentORM", back_populates="outcomes")
    action_plan = relationship("ActionPlanORM", back_populates="outcomes")

    __table_args__ = (
        Index("idx_outcomes_incident_action", "incident_id", "action_id"),
    )
