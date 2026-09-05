"""Fake AI provider for deterministic testing.

The provider implements the :class:`AIProvider` abstract interface but does not make any
network calls. It can be configured with canned responses for both text generation
and structured JSON generation. Errors can be injected to exercise the gateway's
retry and error‑normalisation logic.
"""

import json
import re
from typing import Any, Dict, List, Optional
from uuid import uuid4

from app.ai.errors import (
    AIAuthenticationError,
    AIConfigError,
    AIProviderUnavailableError,
    AIRateLimitError,
    AITimeoutError,
    AITransientError,
)
from app.ai.schemas.messages import ChatMessage, GenerationResponse
from app.ai.schemas.tools import ToolDefinition
from app.ai.ports.provider import AIProvider


class FakeProvider(AIProvider):
    """A lightweight in‑memory provider used for unit tests and deterministic offline execution.

    Configuration attributes can be set after instantiation to control the
    behaviour of ``generate_text`` and ``generate_structured_json``.
    """

    def __init__(self) -> None:
        # Simple deterministic state – callers may override these attributes.
        self.canned_text: str = "default response"
        self.canned_tool_calls: Optional[List[Dict[str, Any]]] = None
        self.canned_json: Optional[str] = None
        # Flags to simulate errors on the next call.
        self.next_error: Optional[Exception] = None
        self._supports_structured = True
        self._supports_tools = True

    # ---------------------------------------------------------------------
    # Capability flags
    # ---------------------------------------------------------------------
    @property
    def provider_name(self) -> str:
        return "fake"

    @property
    def supports_structured_output(self) -> bool:
        return self._supports_structured

    @property
    def supports_tools(self) -> bool:
        return self._supports_tools

    # ---------------------------------------------------------------------
    # Helper to optionally raise a configured error
    # ---------------------------------------------------------------------
    def _maybe_raise_error(self) -> None:
        if self.next_error:
            exc = self.next_error
            self.next_error = None  # reset after raising once
            raise exc

    # ---------------------------------------------------------------------
    # AIProvider contract implementation
    # ---------------------------------------------------------------------
    async def generate_text(
        self,
        messages: List[ChatMessage],
        model: Optional[str] = None,
        temperature: float = 0.0,
        max_tokens: Optional[int] = None,
        tools: Optional[List[ToolDefinition]] = None,
        tool_choice: Optional[str] = None,
        timeout_seconds: Optional[float] = None,
    ) -> GenerationResponse:
        self._maybe_raise_error()
        # In a fake provider we ignore the input messages – deterministic output.
        resp = GenerationResponse(
            content=self.canned_text,
            usage={"prompt_tokens": 5, "completion_tokens": 10, "total_tokens": 15},
            tool_calls=self.canned_tool_calls,
        )
        return resp

    async def generate_structured_json(
        self,
        messages: List[ChatMessage],
        response_schema: Dict[str, Any],
        model: Optional[str] = None,
        temperature: float = 0.0,
        max_tokens: Optional[int] = None,
        timeout_seconds: Optional[float] = None,
    ) -> str:
        self._maybe_raise_error()
        # Explicit override takes precedence if set by a test
        if self.canned_json is not None:
            return self.canned_json

        return self._generate_default_structured_json(messages, response_schema)

    def _generate_default_structured_json(
        self,
        messages: List[ChatMessage],
        response_schema: Dict[str, Any],
    ) -> str:
        full_text = " ".join([m.content for m in messages if m.content])

        # Extract incident_id if present in prompt
        inc_id_match = re.search(r"Incident ID:\s*([0-9a-fA-F-]{36})", full_text)
        incident_id_str = inc_id_match.group(1) if inc_id_match else str(uuid4())

        # Extract incident_type if present in prompt
        inc_type_match = re.search(r"Incident Type:\s*([a-zA-Z0-9_]+)", full_text)
        incident_type = inc_type_match.group(1).lower() if inc_type_match else "payment_drop_spike"

        schema_title = response_schema.get("title", "")
        properties = response_schema.get("properties", {})

        # 1. InvestigationResult schema matching
        if schema_title == "InvestigationResult" or "primary_cause" in properties:
            if incident_type == "payment_drop_spike":
                return json.dumps({
                    "incident_id": incident_id_str,
                    "primary_cause": "HDFC gateway netbanking 504 timeout disruption",
                    "secondary_causes": ["Upstream banking provider latency"],
                    "confidence": 0.94,
                    "confidence_rationale": "Diagnostic telemetry correlates with elevated 504 error rates on primary HDFC netbanking route.",
                    "affected_cohorts": ["HDFC_NETBANKING"],
                    "evidence_keys_used": ["gateway_telemetry_stream", "payment_core_logs"],
                    "is_conclusive": True,
                })
            elif incident_type == "authorization_failure_surge":
                return json.dumps({
                    "incident_id": incident_id_str,
                    "primary_cause": "Card issuer network unavailability on Visa recurring subscriptions",
                    "secondary_causes": ["Card network decline code ISSUER_UNAVAILABLE_05"],
                    "confidence": 0.91,
                    "confidence_rationale": "Statistical anomaly monitor identified surge in issuer unavailable declines.",
                    "affected_cohorts": ["CARDS_VISA_RECURRING"],
                    "evidence_keys_used": ["card_network_monitor"],
                    "is_conclusive": True,
                })
            elif incident_type == "webhook_latency_spike":
                return json.dumps({
                    "incident_id": incident_id_str,
                    "primary_cause": "Merchant webhook delivery latency degradation exceeding dispatch timeout",
                    "secondary_causes": [],
                    "confidence": 0.92,
                    "confidence_rationale": "API traces confirm p99 delivery latency spiked to 18.2s causing dispatch timeouts.",
                    "affected_cohorts": ["MERCHANT_WEBHOOKS"],
                    "evidence_keys_used": ["webhook_dispatcher"],
                    "is_conclusive": True,
                })
            elif incident_type == "settlement_delay":
                return json.dumps({
                    "incident_id": incident_id_str,
                    "primary_cause": "Nodal account settlement batch processing delay at partner bank",
                    "secondary_causes": [],
                    "confidence": 0.88,
                    "confidence_rationale": "Log excerpts indicate settlement reconciliation queue processing delay.",
                    "affected_cohorts": ["NODAL_SETTLEMENTS"],
                    "evidence_keys_used": ["settlement_core_logs"],
                    "is_conclusive": True,
                })
            else:
                return json.dumps({
                    "incident_id": incident_id_str,
                    "primary_cause": f"Operational anomaly attributed to {incident_type}",
                    "secondary_causes": [],
                    "confidence": 0.85,
                    "confidence_rationale": "Diagnostic evidence correlates with observed revenue disruption.",
                    "affected_cohorts": ["DEFAULT_COHORT"],
                    "evidence_keys_used": ["telemetry_stream"],
                    "is_conclusive": True,
                })

        # 2. RecoveryPlanProposal schema matching
        if schema_title == "RecoveryPlanProposal" or "action_type" in properties:
            if incident_type == "payment_drop_spike":
                return json.dumps({
                    "action_type": "gateway_reroute",
                    "target": "gateway_axis_secondary",
                    "expected_recovery_ratio": 0.70,
                    "risk_level": "low",
                    "confidence": 0.90,
                    "rationale": "Reroute checkout traffic to secondary Axis bank gateway to bypass primary HDFC rail outage.",
                })
            elif incident_type == "authorization_failure_surge":
                return json.dumps({
                    "action_type": "retry_payment",
                    "target": "cards_visa_recurring",
                    "expected_recovery_ratio": 0.80,
                    "risk_level": "high",
                    "confidence": 0.88,
                    "rationale": "Schedule smart retries with exponential backoff for impacted recurring subscription payments.",
                })
            elif incident_type == "webhook_latency_spike":
                return json.dumps({
                    "action_type": "webhook_resync",
                    "target": "merchant_webhook_dispatcher",
                    "expected_recovery_ratio": 0.95,
                    "risk_level": "low",
                    "confidence": 0.92,
                    "rationale": "Replay unacknowledged webhook events with increased timeout threshold.",
                })
            elif incident_type == "settlement_delay":
                return json.dumps({
                    "action_type": "merchant_alert",
                    "target": "merchant_ops_channel",
                    "expected_recovery_ratio": 0.50,
                    "risk_level": "low",
                    "confidence": 0.85,
                    "rationale": "Notify merchant operations team regarding banking settlement batch delay.",
                })
            else:
                return json.dumps({
                    "action_type": "gateway_reroute",
                    "target": "secondary_rail",
                    "expected_recovery_ratio": 0.70,
                    "risk_level": "low",
                    "confidence": 0.85,
                    "rationale": "Execute standard bounded mitigation action plan.",
                })

        # 3. Fallback generic schema filler
        fallback_obj: Dict[str, Any] = {}
        for prop_name, prop_def in properties.items():
            prop_type = prop_def.get("type")
            if prop_type == "string":
                fallback_obj[prop_name] = f"mock_{prop_name}"
            elif prop_type in ("number", "integer"):
                fallback_obj[prop_name] = 0.5 if prop_type == "number" else 1
            elif prop_type == "boolean":
                fallback_obj[prop_name] = True
            elif prop_type == "array":
                fallback_obj[prop_name] = []
            elif prop_type == "object":
                fallback_obj[prop_name] = {}
        return json.dumps(fallback_obj)
