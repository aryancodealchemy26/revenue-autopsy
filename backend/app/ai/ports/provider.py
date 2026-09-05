from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Type

from app.ai.schemas.messages import ChatMessage, GenerationResponse
from app.ai.schemas.tools import ToolDefinition


class AIProvider(ABC):
    """Abstract provider interface for LLM services.

    Implementations must be async and must not leak provider-specific types
    into the application layer.
    """

    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Human readable identifier (e.g., 'openai', 'fake')."""
        ...

    @property
    @abstractmethod
    def supports_structured_output(self) -> bool:
        """Return True if the provider can return native JSON/structured output."""
        ...

    @property
    @abstractmethod
    def supports_tools(self) -> bool:
        """Return True if the provider can emit tool-call objects."""
        ...

    @abstractmethod
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
        """Generate a text completion or tool-call request.

        Must return a :class:`GenerationResponse` containing the raw content,
        optional usage metadata and any tool call structures.
        """
        ...

    @abstractmethod
    async def generate_structured_json(
        self,
        messages: List[ChatMessage],
        response_schema: Dict[str, Any],
        model: Optional[str] = None,
        temperature: float = 0.0,
        max_tokens: Optional[int] = None,
        timeout_seconds: Optional[float] = None,
    ) -> str:
        """Generate a JSON string that conforms to *response_schema*.

        The raw string is returned; the caller is responsible for parsing
        and validating against a Pydantic model.
        """
        ...
