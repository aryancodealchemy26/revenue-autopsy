"""Fake AI provider for deterministic testing.

The provider implements the :class:`AIProvider` abstract interface but does not make any
network calls. It can be configured with canned responses for both text generation
and structured JSON generation. Errors can be injected to exercise the gateway's
retry and error‑normalisation logic.
"""

import json
import random
from typing import Any, Dict, List, Optional

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
    """A lightweight in‑memory provider used for unit tests.

    Configuration attributes can be set after instantiation to control the
    behaviour of ``generate_text`` and ``generate_structured_json``.
    """

    def __init__(self) -> None:
        # Simple deterministic state – callers may override these attributes.
        self.canned_text: str = "default response"
        self.canned_tool_calls: Optional[List[Dict[str, Any]]] = None
        self.canned_json: str = "{}"
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
        # The fake simply returns the pre‑set JSON string. Tests may replace it.
        return self.canned_json
