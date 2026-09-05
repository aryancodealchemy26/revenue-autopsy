"""Tests for provider adapter contracts, factory, and FastAPI dependency."""

from unittest.mock import AsyncMock, MagicMock, patch
import pytest
from pydantic import SecretStr

from app.ai.errors import AIConfigError
from app.ai.gateway import AIGateway
from app.ai.ports.provider import AIProvider
from app.ai.providers.factory import get_provider
from app.ai.providers.fake_provider import FakeProvider
from app.ai.providers.openai_provider import OpenAIProvider
from app.ai.schemas.messages import ChatMessage, MessageRole
from app.api.dependencies.ai import get_ai_gateway
from app.core.config import Settings


@pytest.mark.anyio
async def test_fake_provider_contract():
    """Verify FakeProvider satisfies AIProvider interface."""
    provider = FakeProvider()
    assert isinstance(provider, AIProvider)
    assert provider.provider_name == "fake"
    assert provider.supports_structured_output is True
    assert provider.supports_tools is True

    provider.canned_text = "Hermetic result"
    resp = await provider.generate_text([ChatMessage(role=MessageRole.user, content="test")])
    assert resp.content == "Hermetic result"


@pytest.mark.anyio
async def test_openai_provider_mocked_contract():
    """Verify OpenAIProvider correctly interacts with AsyncOpenAI client."""
    provider = OpenAIProvider(api_key="test-sk-key")
    assert isinstance(provider, AIProvider)
    assert provider.provider_name == "openai"

    mock_choice = MagicMock()
    mock_choice.message.content = "Mocked OpenAI response"
    mock_choice.message.tool_calls = None

    mock_resp = MagicMock()
    mock_resp.choices = [mock_choice]
    mock_resp.usage = MagicMock(prompt_tokens=10, completion_tokens=20, total_tokens=30)

    provider._client = MagicMock()
    provider._client.chat = MagicMock()
    provider._client.chat.completions = MagicMock()
    provider._client.chat.completions.create = AsyncMock(return_value=mock_resp)

    messages = [ChatMessage(role=MessageRole.user, content="test")]
    result = await provider.generate_text(messages=messages)

    assert result.content == "Mocked OpenAI response"
    assert result.usage == {"prompt_tokens": 10, "completion_tokens": 20, "total_tokens": 30}


from app.core.config import settings


def test_provider_factory_fake():
    """Verify factory returns FakeProvider when LLM_PROVIDER is fake."""
    with patch.object(settings, "LLM_PROVIDER", "fake"):
        provider = get_provider()
        assert isinstance(provider, FakeProvider)


def test_provider_factory_openai():
    """Verify factory returns OpenAIProvider when LLM_PROVIDER is openai."""
    with patch.object(settings, "LLM_PROVIDER", "openai"), \
         patch.object(settings, "LLM_API_KEY", SecretStr("test-key")), \
         patch.object(settings, "LLM_BASE_URL", "https://api.openai.com/v1"):
        provider = get_provider()
        assert isinstance(provider, OpenAIProvider)
        assert provider.base_url == "https://api.openai.com/v1"


def test_provider_factory_invalid():
    """Verify factory raises AIConfigError for unknown provider."""
    with patch.object(settings, "LLM_PROVIDER", "unsupported_provider"):
        with pytest.raises(AIConfigError) as exc_info:
            get_provider()
        assert "Unsupported LLM provider" in str(exc_info.value)


def test_fastapi_ai_dependency():
    """Verify get_ai_gateway dependency returns configured AIGateway."""
    gateway = get_ai_gateway()
    assert isinstance(gateway, AIGateway)
    assert isinstance(gateway._provider, FakeProvider)
