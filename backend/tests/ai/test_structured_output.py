"""Tests for AIGateway structured Pydantic output validation and malformed recovery."""

from decimal import Decimal
from typing import List
import pytest
from pydantic import BaseModel, Field

from app.ai.errors import (
    AIMalformedResponseError,
    AIStructuredOutputValidationError,
)
from app.ai.gateway import AIGateway
from app.ai.providers.fake_provider import FakeProvider
from app.ai.schemas.messages import ChatMessage, MessageRole


class InvestigationReport(BaseModel):
    root_cause: str = Field(..., description="Root cause description")
    confidence: float = Field(..., ge=0.0, le=1.0)
    suggested_fixes: List[str] = Field(default_factory=list)


@pytest.mark.anyio
async def test_generate_structured_success():
    """Verify structured generation parses valid JSON into typed Pydantic model."""
    provider = FakeProvider()
    provider.canned_json = (
        '{"root_cause": "Webhook signature mismatch", "confidence": 0.95, "suggested_fixes": ["Rotate secret"]}'
    )
    gateway = AIGateway(provider=provider, default_model="gpt-4o-mini")

    messages = [ChatMessage(role=MessageRole.user, content="Generate investigation report")]
    report = await gateway.generate_structured(
        messages=messages,
        response_model=InvestigationReport,
        correlation_id="corr-struct-01",
    )

    assert isinstance(report, InvestigationReport)
    assert report.root_cause == "Webhook signature mismatch"
    assert report.confidence == 0.95
    assert report.suggested_fixes == ["Rotate secret"]


@pytest.mark.anyio
async def test_generate_structured_validation_error():
    """Verify schema mismatch (e.g. out-of-range confidence) raises AIStructuredOutputValidationError."""
    provider = FakeProvider()
    provider.canned_json = '{"root_cause": "Unknown", "confidence": 1.5}'  # confidence > 1.0 violates schema
    gateway = AIGateway(provider=provider, default_model="gpt-4o-mini")

    messages = [ChatMessage(role=MessageRole.user, content="Generate report")]
    with pytest.raises(AIStructuredOutputValidationError):
        await gateway.generate_structured(messages=messages, response_model=InvestigationReport)
