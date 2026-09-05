"""Incident domain enums."""

from enum import Enum


class IncidentType(str, Enum):
    """Classification of detected revenue anomaly or incident."""

    PAYMENT_DROP_SPIKE = "payment_drop_spike"
    AUTHORIZATION_FAILURE_SURGE = "authorization_failure_surge"
    SETTLEMENT_DELAY = "settlement_delay"
    DISPUTE_SPIKE = "dispute_spike"
    WEBHOOK_LATENCY_SPIKE = "webhook_latency_spike"


class IncidentSeverity(str, Enum):
    """Impact severity level of an incident."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class IncidentStatus(str, Enum):
    """Lifecycle status of a revenue incident."""

    DETECTED = "detected"
    INVESTIGATING = "investigating"
    ACTION_PROPOSED = "action_proposed"
    ACTION_APPROVED = "action_approved"
    RESOLVED = "resolved"
    CLOSED = "closed"


class EvidenceType(str, Enum):
    """Type of supporting diagnostic evidence gathered for an incident."""

    TELEMETRY_METRIC = "telemetry_metric"
    LOG_EXCERPT = "log_excerpt"
    API_TRACE = "api_trace"
    STATISTICAL_ANOMALY = "statistical_anomaly"
