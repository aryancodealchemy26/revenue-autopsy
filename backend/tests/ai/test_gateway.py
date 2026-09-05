"""Tests for AIGateway orchestration, defaults, and telemetry."""

import pytest
from app.ai.gateway import AIGateway
from app.ai.providers.fake_provider import FakeProvider
from app.ai.schemas.messages import ChatMessage, MessageRole


@pytest.mark.anyio
async def test_gateway_generate_text_default_model():
    """Verify gateway generation using FakeProvider with default model."""
    provider = FakeProvider()
    provider.canned_text = "Analysis complete: Payment gateway degraded."
    gateway = AIGateway(provider=provider, default_model="gpt-4o-mini")

    messages = [
        ChatMessage(role=MessageRole.system, content="You are a root cause analysis assistant."),
        ChatMessage(role=MessageRole.user, content="Investigate incident #123."),
    ]
    response = await gateway.generate(messages=messages, correlation_id="corr-001")

    assert response.content == "Analysis complete: Payment gateway degraded."
    assert response.usage is not None
    assert response.usage["total_tokens"] == 15


@pytest.mark.anyio
async def test_gateway_generate_with_model_override():
    """Verify gateway generation allows per-request model override."""
    provider = FakeProvider()
    provider.canned_text = "Custom model output"
    gateway = AIGateway(provider=provider, default_model="gpt-4o-mini")

    messages = [ChatMessage(role=MessageRole.user, content="Ping")]
    response = await gateway.generate(messages=messages, model="custom-gpt-4o")

    assert response.content == "Custom model output"
