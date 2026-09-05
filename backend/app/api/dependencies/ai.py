"""FastAPI dependency provider for AIGateway."""

from app.core.config import settings
from app.ai.gateway import AIGateway
from app.ai.providers.factory import get_provider


def get_ai_gateway() -> AIGateway:
    """Dependency provider that instantiates and returns the configured AIGateway."""
    provider = get_provider()
    return AIGateway(
        provider=provider,
        default_model=settings.LLM_MODEL,
        timeout_seconds=settings.LLM_TIMEOUT_SECONDS,
        max_retries=settings.LLM_MAX_RETRIES,
        backoff_factor=settings.LLM_BACKOFF_FACTOR,
    )
