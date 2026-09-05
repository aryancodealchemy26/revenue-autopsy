"""Initial schema creation for Revenue Autopsy persistence layer.

Revision ID: 001_initial_schema
Revises: 
Create Date: 2026-09-05 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "001_initial_schema"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. merchants table
    op.create_table(
        "merchants",
        sa.Column("merchant_id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("currency", sa.String(length=3), nullable=False, server_default="INR"),
        sa.Column("timezone", sa.String(length=64), nullable=False, server_default="Asia/Kolkata"),
        sa.Column("status", sa.String(length=32), nullable=False, server_default="active"),
    )

    # 2. revenue_events table
    op.create_table(
        "revenue_events",
        sa.Column("event_id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("merchant_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("merchants.merchant_id", ondelete="CASCADE"), nullable=False),
        sa.Column("event_type", sa.String(length=64), nullable=False),
        sa.Column("source", sa.String(length=255), nullable=False),
        sa.Column("timestamp", sa.DateTime(timezone=True), nullable=False),
        sa.Column("amount", sa.Numeric(precision=18, scale=4), nullable=False),
        sa.Column("currency", sa.String(length=3), nullable=False, server_default="INR"),
        sa.Column("metadata_json", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
    )
    op.create_index("idx_revenue_events_merchant_ts", "revenue_events", ["merchant_id", "timestamp"])
    op.create_index("idx_revenue_events_type", "revenue_events", ["event_type"])

    # 3. incidents table
    op.create_table(
        "incidents",
        sa.Column("incident_id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("merchant_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("merchants.merchant_id", ondelete="CASCADE"), nullable=False),
        sa.Column("incident_type", sa.String(length=64), nullable=False),
        sa.Column("severity", sa.String(length=32), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False, server_default="detected"),
        sa.Column("detected_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("revenue_at_risk", sa.Numeric(precision=18, scale=4), nullable=False),
        sa.Column("currency", sa.String(length=3), nullable=False, server_default="INR"),
        sa.Column("confidence", sa.Numeric(precision=5, scale=4), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
    )
    op.create_index("idx_incidents_merchant_status", "incidents", ["merchant_id", "status"])

    # 4. evidence table
    op.create_table(
        "evidence",
        sa.Column("evidence_id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("incident_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("incidents.incident_id", ondelete="CASCADE"), nullable=False),
        sa.Column("evidence_type", sa.String(length=64), nullable=False),
        sa.Column("source", sa.String(length=255), nullable=False),
        sa.Column("observed_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("summary", sa.Text(), nullable=False),
        sa.Column("metrics_data_json", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
    )
    op.create_index("idx_evidence_incident_obs", "evidence", ["incident_id", "observed_at"])

    # 5. action_plans table
    op.create_table(
        "action_plans",
        sa.Column("action_id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("incident_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("incidents.incident_id", ondelete="CASCADE"), nullable=False),
        sa.Column("action_type", sa.String(length=64), nullable=False),
        sa.Column("target", sa.String(length=255), nullable=False),
        sa.Column("expected_recovery", sa.Numeric(precision=18, scale=4), nullable=False),
        sa.Column("currency", sa.String(length=3), nullable=False, server_default="INR"),
        sa.Column("risk_level", sa.String(length=32), nullable=False),
        sa.Column("confidence", sa.Numeric(precision=5, scale=4), nullable=False),
        sa.Column("approval_required", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("status", sa.String(length=32), nullable=False, server_default="proposed"),
        sa.Column("rationale", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("idx_actions_incident_status", "action_plans", ["incident_id", "status"])

    # 6. outcomes table
    op.create_table(
        "outcomes",
        sa.Column("outcome_id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("incident_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("incidents.incident_id", ondelete="CASCADE"), nullable=False),
        sa.Column("action_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("action_plans.action_id", ondelete="CASCADE"), nullable=False),
        sa.Column("outcome_type", sa.String(length=64), nullable=False),
        sa.Column("amount", sa.Numeric(precision=18, scale=4), nullable=False),
        sa.Column("currency", sa.String(length=3), nullable=False, server_default="INR"),
        sa.Column("status", sa.String(length=32), nullable=False, server_default="measured"),
        sa.Column("measured_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("reference_data_json", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
    )
    op.create_index("idx_outcomes_incident_action", "outcomes", ["incident_id", "action_id"])


def downgrade() -> None:
    op.drop_table("outcomes")
    op.drop_table("action_plans")
    op.drop_table("evidence")
    op.drop_table("incidents")
    op.drop_table("revenue_events")
    op.drop_table("merchants")
