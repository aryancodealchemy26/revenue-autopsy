"""Base provider class offering shared utilities for AI providers.

This class implements the AIProvider abstract interface defined in
`app.ai.ports.provider`. Concrete providers (FakeProvider, OpenAIProvider)
inherit from this base to reuse common initialisation and error‑handling
helpers.
"""

import logging
from typing import Optional

from app.ai.errors import (
    AIAuthenticationError,
    AIConfigError,
    AIProviderUnavailableError,
    AIRateLimitError,
    AITimeoutError,
    AITransientError,
)
from app.ai.schemas.messages import GenerationResponse, ChatMessage
from app.ai.schemas.tools import ToolDefinition
from app.ai.ports.provider import AIProvider

logger = logging.getLogger(__name__)


class BaseProvider(AIProvider):
    """Minimal shared implementation for AI providers.

    The class stores API credentials and a base URL. Sub‑classes must implement
    the abstract ``generate_text`` and ``generate_structured_json`` methods.
    """

    def __init__(self, *, api_key: Optional[str] = None, base_url: Optional[str] = None):
        self.api_key = api_key
        self.base_url = base_url
        logger.debug(
            "%s initialized – api_key set: %s, base_url=%s",
            self.__class__.__name__,
            bool(api_key),
            base_url,
        )

    # Provider name and capability flags are left abstract for concrete classes.

    @staticmethod
    def _wrap_transient_error(exc: Exception) -> AITransientError:
        """Convert a generic exception into a lightweight ``AITransientError``.

        Concrete adapters should call this when catching low‑level network
        failures (e.g., ``httpx.HTTPError``) to map them into the gateway's
        retryable error hierarchy.
        """
        return AITransientError(str(exc))

    # The ``generate_text`` and ``generate_structured_json`` methods remain abstract
    # and will be provided by each concrete provider implementation.
