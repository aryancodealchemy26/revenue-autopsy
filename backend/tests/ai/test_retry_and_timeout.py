"""Tests for bounded exponential retries and timeout behavior in AIGateway."""

import asyncio
from unittest.mock import AsyncMock, patch
import pytest

from app.ai.errors import (
    AIAuthenticationError,
    AIRateLimitError,
    AITimeoutError,
)
from app.ai.gateway import AIGateway
from app.ai.providers.fake_provider import FakeProvider
from app.ai.schemas.messages import ChatMessage, GenerationResponse, MessageRole


@pytest.mark.anyio
async def test_retry_on_transient_error_eventual_success():
    """Verify gateway retries on transient rate limit and succeeds on subsequent try."""
    provider = FakeProvider()
    call_count = 0

    async def flaky_generate(*args, **kwargs):
        nonlocal call_count
        call_count += 1
        if call_count == 1:
            raise AIRateLimitError("Simulated 429")
        return GenerationResponse(content="Success after retry")

    provider.generate_text = flaky_generate

    gateway = AIGateway(
        provider=provider,
        default_model="gpt-4o-mini",
        max_retries=2,
        backoff_factor=0.01,  # Fast backoff for test
    )

    messages = [ChatMessage(role=MessageRole.user, content="Ping")]
    response = await gateway.generate(messages=messages)

    assert response.content == "Success after retry"
    assert call_count == 2


@pytest.mark.anyio
async def test_retry_exhaustion_raises():
    """Verify exceeding max_retries on transient errors raises the exception."""
    provider = FakeProvider()

    async def always_fail(*args, **kwargs):
        raise AIRateLimitError("Persistent 429")

    provider.generate_text = always_fail

    gateway = AIGateway(
        provider=provider,
        default_model="gpt-4o-mini",
        max_retries=2,
        backoff_factor=0.01,
    )

    messages = [ChatMessage(role=MessageRole.user, content="Ping")]
    with pytest.raises(AIRateLimitError):
        await gateway.generate(messages=messages)


@pytest.mark.anyio
async def test_non_retryable_error_aborts_immediately():
    """Verify non-retryable errors (e.g. AIAuthenticationError) do not retry."""
    provider = FakeProvider()
    call_count = 0

    async def auth_fail(*args, **kwargs):
        nonlocal call_count
        call_count += 1
        raise AIAuthenticationError("Invalid credentials")

    provider.generate_text = auth_fail

    gateway = AIGateway(
        provider=provider,
        default_model="gpt-4o-mini",
        max_retries=3,
        backoff_factor=0.01,
    )

    messages = [ChatMessage(role=MessageRole.user, content="Ping")]
    with pytest.raises(AIAuthenticationError):
        await gateway.generate(messages=messages)

    assert call_count == 1  # No retry attempted
