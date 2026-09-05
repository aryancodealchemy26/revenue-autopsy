"""Revenue Investigator Agent coordinating root-cause analysis via AIGateway."""

import json
from decimal import Decimal
from typing import List, Optional

from app.agents.investigator.schemas import InvestigationResult
from app.ai.gateway import AIGateway
from app.ai.schemas.messages import ChatMessage, MessageRole
from app.domain.incidents.models import Evidence


INVESTIGATOR_SYSTEM_PROMPT = """You are the Revenue Incident Investigator Agent for Revenue Autopsy.
Your sole purpose is to analyze revenue incidents, reason strictly over provided deterministic diagnostic evidence, and determine the root cause.

STRICT OPERATIONAL RULES:
1. You must ONLY reason over the provided telemetry metrics, log excerpts, and API traces.
2. Do NOT invent or hallucinate metrics, error codes, payment counts, or financial numbers.
3. The revenue at risk has already been computed deterministically and is an invariant fact.
4. Assess confidence honestly based on available evidence. If the evidence is contradictory, missing, or inconclusive, set `is_conclusive` to False and provide your rationale.
5. Identify impacted cohorts (e.g. specific payment methods, banks, card networks).
"""


class InvestigatorAgent:
    """Agent responsible for revenue incident root-cause attribution."""

    def __init__(self, gateway: AIGateway, model: Optional[str] = None):
        self._gateway = gateway
        self._model = model

    def _build_prompt_content(
        self,
        incident_id: str,
        merchant_id: str,
        incident_type: str,
        severity: str,
        revenue_at_risk: str,
        currency: str,
        description: str,
        evidences: List[Evidence],
    ) -> str:
        evidence_descriptions = []
        for i, ev in enumerate(evidences, 1):
            metrics_str = json.dumps(ev.metrics_data) if ev.metrics_data else "{}"
            evidence_descriptions.append(
                f"[{i}] Type: {ev.evidence_type.value} | Source: {ev.source}\n"
                f"    Summary: {ev.summary}\n"
                f"    Metrics: {metrics_str}"
            )

        evidence_section = "\n".join(evidence_descriptions) if evidence_descriptions else "NO EVIDENCE PROVIDED."

        return (
            f"=== INCIDENT CONTEXT ===\n"
            f"Incident ID: {incident_id}\n"
            f"Merchant ID: {merchant_id}\n"
            f"Incident Type: {incident_type}\n"
            f"Severity: {severity}\n"
            f"Deterministic Revenue at Risk: {currency} {revenue_at_risk}\n"
            f"Description: {description}\n\n"
            f"=== DIAGNOSTIC EVIDENCE ===\n"
            f"{evidence_section}\n\n"
            f"Provide your structured root cause investigation result."
        )

    async def investigate(
        self,
        incident_id: str,
        merchant_id: str,
        incident_type: str,
        severity: str,
        revenue_at_risk: Decimal,
        currency: str,
        description: str,
        evidences: List[Evidence],
        correlation_id: Optional[str] = None,
    ) -> InvestigationResult:
        """Execute investigation reasoning over grounded evidence via AIGateway."""
        prompt_content = self._build_prompt_content(
            incident_id=incident_id,
            merchant_id=merchant_id,
            incident_type=incident_type,
            severity=severity,
            revenue_at_risk=str(revenue_at_risk),
            currency=currency,
            description=description,
            evidences=evidences,
        )

        messages = [
            ChatMessage(role=MessageRole.system, content=INVESTIGATOR_SYSTEM_PROMPT),
            ChatMessage(role=MessageRole.user, content=prompt_content),
        ]

        result = await self._gateway.generate_structured(
            messages=messages,
            response_model=InvestigationResult,
            model=self._model,
            correlation_id=correlation_id,
        )

        # Enforce fail-closed confidence rule: If confidence is below threshold (< 0.40) or no evidence, mark inconclusive
        if not evidences or result.confidence < Decimal("0.40"):
            result = InvestigationResult(
                incident_id=result.incident_id,
                primary_cause=result.primary_cause,
                secondary_causes=result.secondary_causes,
                confidence=result.confidence,
                confidence_rationale=result.confidence_rationale,
                affected_cohorts=result.affected_cohorts,
                evidence_keys_used=result.evidence_keys_used,
                is_conclusive=False,
            )

        return result
