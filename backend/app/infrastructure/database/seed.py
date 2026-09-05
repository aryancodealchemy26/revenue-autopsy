"""Programmatic Development & Demo Database Seeder.

Seeds deterministic sandbox merchant and the 4 canonical demo incidents (with diagnostic telemetry evidence)
under strict idempotency for development and testing environments.
"""

from datetime import datetime, timezone, timedelta
from decimal import Decimal
from typing import Any, Dict, List
from uuid import UUID

from app.application.ports.unit_of_work import UnitOfWork
from app.domain.incidents.enums import EvidenceType, IncidentSeverity, IncidentStatus, IncidentType
from app.domain.incidents.models import Evidence, Incident
from app.domain.merchants.enums import MerchantStatus
from app.domain.merchants.models import Merchant

SANDBOX_MERCHANT_ID = UUID("00000000-0000-0000-0000-000000000001")

# Canonical Incident UUIDs
INCIDENT_HDFC_ID = UUID("00000000-0000-0000-0000-000000000101")
INCIDENT_CARD_AUTH_ID = UUID("00000000-0000-0000-0000-000000000102")
INCIDENT_WEBHOOK_LAG_ID = UUID("00000000-0000-0000-0000-000000000103")
INCIDENT_SETTLEMENT_DELAY_ID = UUID("00000000-0000-0000-0000-000000000104")

# Canonical Evidence UUIDs
EV_HDFC_01 = UUID("00000000-0000-0000-0001-000000000101")
EV_HDFC_02 = UUID("00000000-0000-0000-0001-000000000102")
EV_HDFC_03 = UUID("00000000-0000-0000-0001-000000000103")

EV_AUTH_01 = UUID("00000000-0000-0000-0001-000000000201")
EV_AUTH_02 = UUID("00000000-0000-0000-0001-000000000202")

EV_WH_01 = UUID("00000000-0000-0000-0001-000000000301")
EV_SETTLE_01 = UUID("00000000-0000-0000-0001-000000000401")


async def seed_development_data(uow: UnitOfWork) -> Dict[str, Any]:
    """Idempotently seed deterministic sandbox merchant and 4 canonical incidents with evidence."""
    now = datetime.now(timezone.utc)

    # 1. Deterministic Merchant
    merchant = Merchant(
        merchant_id=SANDBOX_MERCHANT_ID,
        name="Acme Digital Commerce Pvt Ltd",
        currency="INR",
        timezone="Asia/Kolkata",
        status=MerchantStatus.ACTIVE,
        created_at=now - timedelta(days=30),
    )
    await uow.merchants.save(merchant)

    # 2. Canonical Demo Incidents
    incidents: List[Incident] = [
        # Scenario 1: HDFC Netbanking Drop (Intended ALLOW scenario)
        Incident(
            incident_id=INCIDENT_HDFC_ID,
            merchant_id=SANDBOX_MERCHANT_ID,
            incident_type=IncidentType.PAYMENT_DROP_SPIKE,
            severity=IncidentSeverity.HIGH,
            status=IncidentStatus.DETECTED,
            detected_at=now - timedelta(minutes=45),
            revenue_at_risk=Decimal("45000.00"),
            currency="INR",
            confidence=Decimal("0.92"),
            description="Severe 84% conversion drop detected on HDFC Netbanking checkout route.",
        ),
        # Scenario 2: Card Auth Surge (Intended REQUIRE_APPROVAL scenario)
        Incident(
            incident_id=INCIDENT_CARD_AUTH_ID,
            merchant_id=SANDBOX_MERCHANT_ID,
            incident_type=IncidentType.AUTHORIZATION_FAILURE_SURGE,
            severity=IncidentSeverity.CRITICAL,
            status=IncidentStatus.DETECTED,
            detected_at=now - timedelta(minutes=30),
            revenue_at_risk=Decimal("125000.00"),
            currency="INR",
            confidence=Decimal("0.89"),
            description="Surge in card authorization rejects on international Visa/Mastercard transactions.",
        ),
        # Scenario 3: Webhook Latency Spike (Intended ALLOW scenario)
        Incident(
            incident_id=INCIDENT_WEBHOOK_LAG_ID,
            merchant_id=SANDBOX_MERCHANT_ID,
            incident_type=IncidentType.WEBHOOK_LATENCY_SPIKE,
            severity=IncidentSeverity.HIGH,
            status=IncidentStatus.DETECTED,
            detected_at=now - timedelta(minutes=20),
            revenue_at_risk=Decimal("18000.00"),
            currency="INR",
            confidence=Decimal("0.91"),
            description="Payment confirmation webhooks delayed by >12 seconds, causing customer drop-off on fulfillment.",
        ),
        # Scenario 4: Settlement Delay (Intended ALLOW scenario)
        Incident(
            incident_id=INCIDENT_SETTLEMENT_DELAY_ID,
            merchant_id=SANDBOX_MERCHANT_ID,
            incident_type=IncidentType.SETTLEMENT_DELAY,
            severity=IncidentSeverity.MEDIUM,
            status=IncidentStatus.DETECTED,
            detected_at=now - timedelta(minutes=10),
            revenue_at_risk=Decimal("8500.00"),
            currency="INR",
            confidence=Decimal("0.82"),
            description="Scheduled batch settlement payout delayed past standard T+1 window.",
        ),
    ]

    for inc in incidents:
        await uow.incidents.save(inc)

    # 3. Canonical Telemetry Evidence Records
    evidences: List[Evidence] = [
        # HDFC Evidence (3 records)
        Evidence(
            evidence_id=EV_HDFC_01,
            incident_id=INCIDENT_HDFC_ID,
            evidence_type=EvidenceType.TELEMETRY_METRIC,
            source="gateway_telemetry_stream",
            observed_at=now - timedelta(minutes=42),
            summary="HDFC Netbanking route timeout rate escalated to 14.8% (baseline: 0.12%).",
            metrics_data={
                "error_rate": 0.148,
                "baseline_rate": 0.0012,
                "affected_gateway": "HDFC_DIRECT",
            },
        ),
        Evidence(
            evidence_id=EV_HDFC_02,
            incident_id=INCIDENT_HDFC_ID,
            evidence_type=EvidenceType.API_TRACE,
            source="razorpay_gateway_logs",
            observed_at=now - timedelta(minutes=40),
            summary="Upstream gateway socket timeout during bank OTP redirection handshake.",
            metrics_data={
                "http_status": 504,
                "p99_latency_ms": 4850,
                "bank_code": "HDFC",
            },
        ),
        Evidence(
            evidence_id=EV_HDFC_03,
            incident_id=INCIDENT_HDFC_ID,
            evidence_type=EvidenceType.STATISTICAL_ANOMALY,
            source="conversion_funnel_monitor",
            observed_at=now - timedelta(minutes=38),
            summary="Completed checkout funnel dropped from 78.4% to 12.1% specifically on mobile web.",
            metrics_data={
                "cohort": "HDFC_NETBANKING_MOBILE",
                "funnel_drop_pct": 84.5,
            },
        ),
        # Card Auth Surge Evidence (2 records)
        Evidence(
            evidence_id=EV_AUTH_01,
            incident_id=INCIDENT_CARD_AUTH_ID,
            evidence_type=EvidenceType.TELEMETRY_METRIC,
            source="card_network_stream",
            observed_at=now - timedelta(minutes=28),
            summary="3DS authentication challenges failing with bank acquirer connection drop.",
            metrics_data={
                "failure_rate": 0.32,
                "impacted_volume": "125000.00",
            },
        ),
        Evidence(
            evidence_id=EV_AUTH_02,
            incident_id=INCIDENT_CARD_AUTH_ID,
            evidence_type=EvidenceType.LOG_EXCERPT,
            source="auth_service_logs",
            observed_at=now - timedelta(minutes=26),
            summary="Acquirer returned error 91: Issuer system down or unavailable.",
            metrics_data={
                "error_code": "91",
                "network": "VISA",
            },
        ),
        # Webhook Lag Evidence (1 record)
        Evidence(
            evidence_id=EV_WH_01,
            incident_id=INCIDENT_WEBHOOK_LAG_ID,
            evidence_type=EvidenceType.TELEMETRY_METRIC,
            source="webhook_delivery_monitor",
            observed_at=now - timedelta(minutes=18),
            summary="P95 webhook delivery latency reached 14,200ms (target: <500ms).",
            metrics_data={
                "p95_latency_ms": 14200,
                "backlog_count": 340,
            },
        ),
        # Settlement Delay Evidence (1 record)
        Evidence(
            evidence_id=EV_SETTLE_01,
            incident_id=INCIDENT_SETTLEMENT_DELAY_ID,
            evidence_type=EvidenceType.TELEMETRY_METRIC,
            source="settlement_pipeline",
            observed_at=now - timedelta(minutes=8),
            summary="Bank holiday processing schedule mismatch for nodal account transfer.",
            metrics_data={
                "nodal_bank": "YES_BANK",
                "delay_hours": 4.5,
            },
        ),
    ]

    for ev in evidences:
        await uow.evidence.save(ev)

    await uow.commit()

    return {
        "merchant": merchant,
        "incidents": incidents,
        "evidences": evidences,
    }
