"""Explicit bidirectional mappers between Pydantic domain models and SQLAlchemy ORM models."""

from datetime import timezone
from app.domain.actions.enums import ActionStatus, ActionType, RiskLevel
from app.domain.actions.models import ActionPlan
from app.domain.incidents.enums import EvidenceType, IncidentSeverity, IncidentStatus, IncidentType
from app.domain.incidents.models import Evidence, Incident
from app.domain.merchants.enums import MerchantStatus
from app.domain.merchants.models import Merchant
from app.domain.outcomes.enums import OutcomeStatus, OutcomeType
from app.domain.outcomes.models import Outcome
from app.domain.revenue.enums import RevenueEventType
from app.domain.revenue.models import RevenueEvent
from app.infrastructure.database.models.action import ActionPlanORM
from app.infrastructure.database.models.incident import EvidenceORM, IncidentORM
from app.infrastructure.database.models.merchant import MerchantORM
from app.infrastructure.database.models.outcome import OutcomeORM
from app.infrastructure.database.models.revenue import RevenueEventORM


def _ensure_timezone(dt):
    """Ensure a datetime object is timezone-aware (UTC)."""
    if dt is not None and (dt.tzinfo is None or dt.tzinfo.utcoffset(dt) is None):
        return dt.replace(tzinfo=timezone.utc)
    return dt


# --- Merchant Mappers ---

def merchant_to_orm(merchant: Merchant) -> MerchantORM:
    """Map domain Merchant entity to MerchantORM model."""
    return MerchantORM(
        merchant_id=merchant.merchant_id,
        name=merchant.name,
        currency=merchant.currency,
        timezone=merchant.timezone,
        status=merchant.status.value,
    )


def orm_to_merchant(orm: MerchantORM) -> Merchant:
    """Map MerchantORM model to domain Merchant entity."""
    return Merchant(
        merchant_id=orm.merchant_id,
        name=orm.name,
        currency=orm.currency,
        timezone=orm.timezone,
        status=MerchantStatus(orm.status),
    )


# --- RevenueEvent Mappers ---

def revenue_event_to_orm(event: RevenueEvent) -> RevenueEventORM:
    """Map domain RevenueEvent entity to RevenueEventORM model."""
    return RevenueEventORM(
        event_id=event.event_id,
        merchant_id=event.merchant_id,
        event_type=event.event_type.value,
        source=event.source,
        timestamp=_ensure_timezone(event.timestamp),
        amount=event.amount,
        currency=event.currency,
        metadata_json=dict(event.metadata),
    )


def orm_to_revenue_event(orm: RevenueEventORM) -> RevenueEvent:
    """Map RevenueEventORM model to domain RevenueEvent entity."""
    return RevenueEvent(
        event_id=orm.event_id,
        merchant_id=orm.merchant_id,
        event_type=RevenueEventType(orm.event_type),
        source=orm.source,
        timestamp=_ensure_timezone(orm.timestamp),
        amount=orm.amount,
        currency=orm.currency,
        metadata=dict(orm.metadata_json or {}),
    )


# --- Incident & Evidence Mappers ---

def incident_to_orm(incident: Incident) -> IncidentORM:
    """Map domain Incident entity to IncidentORM model."""
    return IncidentORM(
        incident_id=incident.incident_id,
        merchant_id=incident.merchant_id,
        incident_type=incident.incident_type.value,
        severity=incident.severity.value,
        status=incident.status.value,
        detected_at=_ensure_timezone(incident.detected_at),
        revenue_at_risk=incident.revenue_at_risk,
        currency=incident.currency,
        confidence=incident.confidence,
        description=incident.description,
    )


def orm_to_incident(orm: IncidentORM) -> Incident:
    """Map IncidentORM model to domain Incident entity."""
    return Incident(
        incident_id=orm.incident_id,
        merchant_id=orm.merchant_id,
        incident_type=IncidentType(orm.incident_type),
        severity=IncidentSeverity(orm.severity),
        status=IncidentStatus(orm.status),
        detected_at=_ensure_timezone(orm.detected_at),
        revenue_at_risk=orm.revenue_at_risk,
        currency=orm.currency,
        confidence=orm.confidence,
        description=orm.description,
    )


def evidence_to_orm(evidence: Evidence) -> EvidenceORM:
    """Map domain Evidence entity to EvidenceORM model."""
    return EvidenceORM(
        evidence_id=evidence.evidence_id,
        incident_id=evidence.incident_id,
        evidence_type=evidence.evidence_type.value,
        source=evidence.source,
        observed_at=_ensure_timezone(evidence.observed_at),
        summary=evidence.summary,
        metrics_data_json=dict(evidence.metrics_data),
    )


def orm_to_evidence(orm: EvidenceORM) -> Evidence:
    """Map EvidenceORM model to domain Evidence entity."""
    return Evidence(
        evidence_id=orm.evidence_id,
        incident_id=orm.incident_id,
        evidence_type=EvidenceType(orm.evidence_type),
        source=orm.source,
        observed_at=_ensure_timezone(orm.observed_at),
        summary=orm.summary,
        metrics_data=dict(orm.metrics_data_json or {}),
    )


# --- ActionPlan Mappers ---

def action_plan_to_orm(plan: ActionPlan) -> ActionPlanORM:
    """Map domain ActionPlan entity to ActionPlanORM model."""
    return ActionPlanORM(
        action_id=plan.action_id,
        incident_id=plan.incident_id,
        action_type=plan.action_type.value,
        target=plan.target,
        expected_recovery=plan.expected_recovery,
        currency=plan.currency,
        risk_level=plan.risk_level.value,
        confidence=plan.confidence,
        approval_required=plan.approval_required,
        status=plan.status.value,
        rationale=plan.rationale,
        created_at=_ensure_timezone(plan.created_at),
    )


def orm_to_action_plan(orm: ActionPlanORM) -> ActionPlan:
    """Map ActionPlanORM model to domain ActionPlan entity."""
    return ActionPlan(
        action_id=orm.action_id,
        incident_id=orm.incident_id,
        action_type=ActionType(orm.action_type),
        target=orm.target,
        expected_recovery=orm.expected_recovery,
        currency=orm.currency,
        risk_level=RiskLevel(orm.risk_level),
        confidence=orm.confidence,
        approval_required=orm.approval_required,
        status=ActionStatus(orm.status),
        rationale=orm.rationale,
        created_at=_ensure_timezone(orm.created_at),
    )


# --- Outcome Mappers ---

def outcome_to_orm(outcome: Outcome) -> OutcomeORM:
    """Map domain Outcome entity to OutcomeORM model."""
    return OutcomeORM(
        outcome_id=outcome.outcome_id,
        incident_id=outcome.incident_id,
        action_id=outcome.action_id,
        outcome_type=outcome.outcome_type.value,
        amount=outcome.amount,
        currency=outcome.currency,
        status=outcome.status.value,
        measured_at=_ensure_timezone(outcome.measured_at),
        reference_data_json=dict(outcome.reference_data),
    )


def orm_to_outcome(orm: OutcomeORM) -> Outcome:
    """Map OutcomeORM model to domain Outcome entity."""
    return Outcome(
        outcome_id=orm.outcome_id,
        incident_id=orm.incident_id,
        action_id=orm.action_id,
        outcome_type=OutcomeType(orm.outcome_type),
        amount=orm.amount,
        currency=orm.currency,
        status=OutcomeStatus(orm.status),
        measured_at=_ensure_timezone(orm.measured_at),
        reference_data=dict(orm.reference_data_json or {}),
    )
