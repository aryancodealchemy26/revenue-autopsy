"""Factory for AIProvider implementations based on Settings.

The factory reads ``Settings.LLM_PROVIDER`` and returns an instance of the
corresponding provider class. Supported providers are ``fake`` and ``openai``.
If an unknown provider is requested, ``AIConfigError`` is raised.
"""

from app.core.config import settings
from app.ai.errors import AIConfigError
from app.ai.ports.provider import AIProvider
from app.ai.providers.fake_provider import FakeProvider
from app.ai.providers.openai_provider import OpenAIProvider


def get_provider() -> AIProvider:
    provider_name = (settings.LLM_PROVIDER or "fake").lower()
    if provider_name == "fake":
        return FakeProvider()
    if provider_name == "openai":
        return OpenAIProvider(
            api_key=settings.LLM_API_KEY.get_secret_value() if settings.LLM_API_KEY else None,
            base_url=settings.LLM_BASE_URL,
        )
    raise AIConfigError(f"Unsupported LLM provider: {settings.LLM_PROVIDER}")
