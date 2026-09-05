"""OpenAI-compatible async provider adapter.

Uses the official ``openai`` library's ``AsyncOpenAI`` client. Supports both
standard text generation (with optional tool calls) and structured JSON
generation via the ``response_format`` parameter introduced in OpenAI API v1.
All provider‑specific exceptions are translated into the normalized error
hierarchy defined in ``app.ai.errors``.
"""

import json
from typing import Any, Dict, List, Optional

import openai
from openai import AsyncOpenAI
from openai import (
    APIConnectionError,
    APIError,
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
    AIMalformedResponseError,
)
from app.ai.schemas.messages import ChatMessage, GenerationResponse
from app.ai.schemas.tools import ToolDefinition
from app.ai.ports.provider import AIProvider


class OpenAIProvider(AIProvider):
    """Adapter for the OpenAI (or compatible) API.

    The constructor accepts an optional ``api_key`` and ``base_url`` – the
    latter can be used to point at Azure OpenAI, Ollama, Groq, etc. when the
    endpoint follows the OpenAI JSON schema.
    """

    def __init__(self, *, api_key: Optional[str] = None, base_url: Optional[str] = None):
        self.api_key = api_key or ""
        self.base_url = base_url
        self._client: AsyncOpenAI = AsyncOpenAI(api_key=self.api_key, base_url=self.base_url)
        self._supports_structured = True
        self._supports_tools = True

    # ---------------------------------------------------------------------
    # Capability flags
    # ---------------------------------------------------------------------
    @property
    def provider_name(self) -> str:
        return "openai"

    @property
    def supports_structured_output(self) -> bool:
        return self._supports_structured

    @property
    def supports_tools(self) -> bool:
        return self._supports_tools

    # ---------------------------------------------------------------------
    # Helper to translate OpenAI SDK exceptions into our error hierarchy
    # ---------------------------------------------------------------------
    def _translate_error(self, exc: Exception) -> None:
        if isinstance(exc, AuthenticationError):
            raise AIAuthenticationError(str(exc)) from exc
        if isinstance(exc, RateLimitError):
            raise AIRateLimitError(str(exc)) from exc
        if isinstance(exc, APITimeoutError):
            raise AITimeoutError(str(exc)) from exc
        if isinstance(exc, APIConnectionError):
            raise AIProviderUnavailableError(str(exc)) from exc
        if isinstance(exc, BadRequestError):
            raise AIConfigError(str(exc)) from exc
        if isinstance(exc, APIError):
            raise AITransientError(str(exc)) from exc
        raise AITransientError(str(exc)) from exc

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
        # Convert internal ChatMessage objects to OpenAI SDK format
        openai_messages = [
            {"role": msg.role.value, "content": msg.content}
            for msg in messages
        ]
        # If tools are provided, translate our schema to the OpenAI tool spec
        openai_tools = None
        if tools:
            openai_tools = []
            for td in tools:
                openai_tools.append(
                    {
                        "type": "function",
                        "function": {
                            "name": td.name,
                            "description": td.description,
                            "parameters": td.parameters_schema,
                        },
                    }
                )
        try:
            response = await self._client.chat.completions.create(
                model=model or "gpt-4o-mini",
                messages=openai_messages,
                temperature=temperature,
                max_tokens=max_tokens,
                tools=openai_tools,
                tool_choice=tool_choice,
                timeout=timeout_seconds,
            )
        except Exception as exc:
            self._translate_error(exc)

        # Extract content and potential tool calls
        choice = response.choices[0]
        content = choice.message.content or ""
        tool_calls = None
        if choice.message.tool_calls:
            tool_calls = []
            for tc in choice.message.tool_calls:
                tool_calls.append(
                    {
                        "id": tc.id,
                        "name": tc.function.name,
                        "arguments": json.loads(tc.function.arguments),
                    }
                )
        # Usage metadata (may be None)
        usage = getattr(response, "usage", None)
        usage_dict = None
        if usage:
            usage_dict = {
                "prompt_tokens": usage.prompt_tokens,
                "completion_tokens": usage.completion_tokens,
                "total_tokens": usage.total_tokens,
            }
        return GenerationResponse(content=content, usage=usage_dict, tool_calls=tool_calls)

    async def generate_structured_json(
        self,
        messages: List[ChatMessage],
        response_schema: Dict[str, Any],
        model: Optional[str] = None,
        temperature: float = 0.0,
        max_tokens: Optional[int] = None,
        timeout_seconds: Optional[float] = None,
    ) -> str:
        openai_messages = [
            {"role": msg.role.value, "content": msg.content}
            for msg in messages
        ]
        # Use OpenAI's json mode via response_format
        response_format = {"type": "json_schema", "json_schema": {"name": "response_schema", "strict": True, "schema": response_schema}}
        try:
            response = await self._client.chat.completions.create(
                model=model or "gpt-4o-mini",
                messages=openai_messages,
                temperature=temperature,
                max_tokens=max_tokens,
                response_format=response_format,
                timeout=timeout_seconds,
            )
        except Exception as exc:
            self._translate_error(exc)
        json_text = response.choices[0].message.content
        if not json_text:
            raise AIMalformedResponseError("Empty response when JSON expected")
        # The provider may wrap JSON in markdown code fences – strip them
        stripped = json_text.strip()
        if stripped.startswith('```'):
            # remove the first line (```json?) and the last line
            lines = stripped.splitlines()
            if len(lines) >= 3:
                stripped = "\n".join(lines[1:-1])
        # Validate that it is parseable JSON; raise if malformed
        try:
            json.loads(stripped)
        except json.JSONDecodeError as je:
            raise AIMalformedResponseError(str(je))
        return stripped
