"""Tests for provider exception normalization to AIGatewayError hierarchy."""

from unittest.mock import AsyncMock, MagicMock
import pytest
from openai import (
    APIConnectionError,
    APITimeoutError,
    AuthenticationError,
    BadRequestError,
    RateLimitError,
)

from app.ai.errors import (
    AIAuthenticationError,
    AIConfigError,
    AIProviderUnavailableError,
    AIRateLimitError,
    AITimeoutError,
    AITransientError,
)
from app.ai.providers.openai_provider import OpenAIProvider
from app.ai.schemas.messages import ChatMessage, MessageRole


@pytest.mark.anyio
async def test_openai_authentication_error_normalization():
    """Verify OpenAI 401 AuthenticationError maps to AIAuthenticationError."""
    provider = OpenAIProvider(api_key="invalid-key")
    provider._client = MagicMock()
    provider._client.chat = MagicMock()
    provider._client.chat.completions = MagicMock()
    provider._client.chat.completions.create = AsyncMock(
        side_effect=AuthenticationError(
            message="Invalid API Key",
            response=MagicMock(status_code=401),
            body=None,
        )
    )

    messages = [ChatMessage(role=MessageRole.user, content="Hello")]
    with pytest.raises(AIAuthenticationError) as exc_info:
        await provider.generate_text(messages=messages)
    assert "Invalid API Key" in str(exc_info.value)


@pytest.mark.anyio
async def test_openai_rate_limit_error_normalization():
    """Verify OpenAI 429 RateLimitError maps to AIRateLimitError."""
    provider = OpenAIProvider(api_key="test-key")
    provider._client = MagicMock()
    provider._client.chat = MagicMock()
    provider._client.chat.completions = MagicMock()
    provider._client.chat.completions.create = AsyncMock(
        side_effect=RateLimitError(
            message="Rate limit exceeded",
            response=MagicMock(status_code=429),
            body=None,
        )
    )

    messages = [ChatMessage(role=MessageRole.user, content="Hello")]
    with pytest.raises(AIRateLimitError):
        await provider.generate_text(messages=messages)


@pytest.mark.anyio
async def test_openai_connection_error_normalization():
    """Verify OpenAI APIConnectionError maps to AIProviderUnavailableError."""
    provider = OpenAIProvider(api_key="test-key")
    provider._client = MagicMock()
    provider._client.chat = MagicMock()
    provider._client.chat.completions = MagicMock()
    provider._client.chat.completions.create = AsyncMock(
        side_effect=APIConnectionError(request=MagicMock())
    )

    messages = [ChatMessage(role=MessageRole.user, content="Hello")]
    with pytest.raises(AIProviderUnavailableError):
        await provider.generate_text(messages=messages)


@pytest.mark.anyio
async def test_openai_timeout_normalization():
    """Verify OpenAI APITimeoutError maps to AITimeoutError."""
    provider = OpenAIProvider(api_key="test-key")
    provider._client = MagicMock()
    provider._client.chat = MagicMock()
    provider._client.chat.completions = MagicMock()
    provider._client.chat.completions.create = AsyncMock(
        side_effect=APITimeoutError(request=MagicMock())
    )

    messages = [ChatMessage(role=MessageRole.user, content="Hello")]
    with pytest.raises(AITimeoutError):
        await provider.generate_text(messages=messages)
