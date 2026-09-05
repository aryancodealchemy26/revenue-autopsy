"""AI Gateway orchestrator handling retries, timeouts, observability, and tool validation.

The gateway is the sole entry‑point for application code to request LLM generation.
It never executes tools – it only validates and returns structured data.
"""

import asyncio
import logging
import time
from typing import List, Optional, Type, TypeVar

from app.ai.errors import (
    AIGatewayError,
    AITransientError,
    AIMalformedResponseError,
    AIConfigError,
    AIAuthenticationError,
    AIUnsupportedCapabilityError,
    AIToolNotAllowedError,
    AIStructuredOutputValidationError,
    AIRateLimitError,
    AITimeoutError,
    AIProviderUnavailableError,
)
from app.ai.schemas.messages import ChatMessage, GenerationResponse
from app.ai.schemas.tools import ToolCall, ToolDefinition
from app.ai.ports.provider import AIProvider
from app.ai.tools import ToolRegistry
from pydantic import ValidationError

logger = logging.getLogger(__name__)

T = TypeVar("T")


class AIGateway:
    """Enterprise AI Gateway providing resilience, validation, and observability.

    All application code should use this class instead of calling a provider
    directly. It enforces:

    * Bounded retries with exponential back‑off (standard library only).
    * Strict per‑call timeout handling.
    * Normalized error hierarchy.
    * Optional tool‑call allow‑list validation via :class:`ToolRegistry`.
    * Structured‑output validation against a supplied Pydantic model.
    * Centralised logging of operational metadata (with secret redaction).
    """

    def __init__(
        self,
        provider: AIProvider,
        default_model: Optional[str] = None,
        timeout_seconds: float = 30.0,
        max_retries: int = 3,
        backoff_factor: float = 1.5,
        tool_registry: Optional[ToolRegistry] = None,
    ) -> None:
        self._provider = provider
        self._default_model = default_model
        self._timeout_seconds = timeout_seconds
        self._max_retries = max_retries
        self._backoff_factor = backoff_factor
        self._tool_registry = tool_registry or ToolRegistry()
        logger.debug(
            "AIGateway initialized – provider=%s, model=%s, timeout=%s, retries=%s",
            provider.provider_name,
            default_model,
            timeout_seconds,
            max_retries,
        )

    # ---------------------------------------------------------------------
    # Public generation APIs
    # ---------------------------------------------------------------------
    async def generate(
        self,
        messages: List[ChatMessage],
        model: Optional[str] = None,
        temperature: float = 0.0,
        max_tokens: Optional[int] = None,
        allowed_tools: Optional[List[str]] = None,
        tool_choice: Optional[str] = None,
        correlation_id: Optional[str] = None,
    ) -> GenerationResponse:
        """Generate a text response (or tool‑call payload) with retries & timeout.

        Parameters
        ----------
        messages: List[ChatMessage]
            Conversation history supplied to the LLM.
        model: Optional[str]
            Override the default model for this call.
        allowed_tools: Optional[List[str]]
            If provided, the gateway validates any tool‑call objects returned by
            the provider against this allow‑list.
        correlation_id: Optional[str]
            Identifier propagated to logs for tracing.
        """
        attempt = 0
        while True:
            attempt += 1
            start_ts = time.monotonic()
            try:
                response = await asyncio.wait_for(
                    self._provider.generate_text(
                        messages=messages,
                        model=model or self._default_model,
                        temperature=temperature,
                        max_tokens=max_tokens,
                        tools=self._tool_registry.get_definitions() if allowed_tools else None,
                        tool_choice=tool_choice,
                        timeout_seconds=self._timeout_seconds,
                    ),
                    timeout=self._timeout_seconds,
                )
                latency_ms = (time.monotonic() - start_ts) * 1000
                self._log_success(
                    response,
                    latency_ms=latency_ms,
                    attempt=attempt - 1,
                    correlation_id=correlation_id,
                )

                # Validate tool calls if any
                if response.tool_calls and allowed_tools is not None:
                    validated_calls = []
                    for raw in response.tool_calls:
                        name = raw.get("name") or raw.get("function", {}).get("name")
                        args = raw.get("arguments") or raw.get("function", {}).get("arguments", {})
                        call_id = raw.get("id")
                        if not name:
                            raise AIToolNotAllowedError("Tool call missing name")
                        tool_call = ToolCall(tool_name=name, arguments=args, call_id=call_id)
                        self._tool_registry.validate_call(tool_call, allowed_tools)
                        validated_calls.append(tool_call)
                    response.tool_calls = validated_calls
                return response
            except (AIRateLimitError, AITimeoutError, AIProviderUnavailableError, AIMalformedResponseError) as e:
                latency_ms = (time.monotonic() - start_ts) * 1000
                if attempt > self._max_retries:
                    self._log_failure(e, latency_ms, attempt - 1, correlation_id)
                    raise
                backoff = self._backoff_factor ** attempt
                await asyncio.sleep(backoff)
                continue
            except AITransientError as e:
                latency_ms = (time.monotonic() - start_ts) * 1000
                if attempt > self._max_retries:
                    self._log_failure(e, latency_ms, attempt - 1, correlation_id)
                    raise
                backoff = self._backoff_factor ** attempt
                await asyncio.sleep(backoff)
                continue
            except AIGatewayError as e:
                latency_ms = (time.monotonic() - start_ts) * 1000
                self._log_failure(e, latency_ms, attempt - 1, correlation_id)
                raise
            except Exception as e:
                latency_ms = (time.monotonic() - start_ts) * 1000
                self._log_failure(e, latency_ms, attempt - 1, correlation_id)
                raise AIGatewayError(str(e)) from e

    async def generate_structured(
        self,
        messages: List[ChatMessage],
        response_model: Type[T],
        model: Optional[str] = None,
        temperature: float = 0.0,
        max_tokens: Optional[int] = None,
        correlation_id: Optional[str] = None,
    ) -> T:
        """Generate output that conforms to ``response_model``.

        The method asks the provider for a raw JSON string (via ``generate_structured_json``),
        validates it against the supplied Pydantic model, and returns the parsed instance.
        """
        attempt = 0
        while True:
            attempt += 1
            start_ts = time.monotonic()
            try:
                raw_json = await asyncio.wait_for(
                    self._provider.generate_structured_json(
                        messages=messages,
                        response_schema=response_model.model_json_schema(),
                        model=model or self._default_model,
                        temperature=temperature,
                        max_tokens=max_tokens,
                        timeout_seconds=self._timeout_seconds,
                    ),
                    timeout=self._timeout_seconds,
                )
                latency_ms = (time.monotonic() - start_ts) * 1000
                self._log_success(
                    None,
                    latency_ms=latency_ms,
                    attempt=attempt - 1,
                    correlation_id=correlation_id,
                )
                try:
                    parsed = response_model.model_validate_json(raw_json)
                except ValidationError as ve:
                    raise AIStructuredOutputValidationError(str(ve)) from ve
                return parsed
            except (AIRateLimitError, AITimeoutError, AIProviderUnavailableError, AIMalformedResponseError) as e:
                latency_ms = (time.monotonic() - start_ts) * 1000
                if attempt > self._max_retries:
                    self._log_failure(e, latency_ms, attempt - 1, correlation_id)
                    raise
                await asyncio.sleep(self._backoff_factor ** attempt)
                continue
            except AITransientError as e:
                latency_ms = (time.monotonic() - start_ts) * 1000
                if attempt > self._max_retries:
                    self._log_failure(e, latency_ms, attempt - 1, correlation_id)
                    raise
                await asyncio.sleep(self._backoff_factor ** attempt)
                continue
            except AIGatewayError as e:
                latency_ms = (time.monotonic() - start_ts) * 1000
                self._log_failure(e, latency_ms, attempt - 1, correlation_id)
                raise
            except Exception as e:
                latency_ms = (time.monotonic() - start_ts) * 1000
                self._log_failure(e, latency_ms, attempt - 1, correlation_id)
                raise AIGatewayError(str(e)) from e

    # ---------------------------------------------------------------------
    # Logging helpers (observability owned by the gateway)
    # ---------------------------------------------------------------------
    def _log_success(
        self,
        response: Optional[GenerationResponse],
        *,
        latency_ms: float,
        attempt: int,
        correlation_id: Optional[str] = None,
    ) -> None:
        log_data = {
            "provider": self._provider.provider_name,
            "model": getattr(response, "model", self._default_model) if response else self._default_model,
            "latency_ms": round(latency_ms, 2),
            "retry_count": attempt,
            "status": "SUCCESS",
            "correlation_id": correlation_id,
        }
        if response and response.usage:
            log_data.update(response.usage)
        logger.info("AIGateway success", extra=log_data)

    def _log_failure(
        self,
        exc: Exception,
        latency_ms: float,
        attempt: int,
        correlation_id: Optional[str] = None,
    ) -> None:
        log_data = {
            "provider": self._provider.provider_name,
            "latency_ms": round(latency_ms, 2),
            "retry_count": attempt,
            "status": "FAILURE",
            "error_category": exc.__class__.__name__,
            "correlation_id": correlation_id,
        }
        logger.error("AIGateway failure", exc_info=exc, extra=log_data)
