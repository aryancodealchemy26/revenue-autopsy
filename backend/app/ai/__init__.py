"""AI layer package."""

from app.ai.errors import (
    AIAuthenticationError,
    AIConfigError,
    AIGatewayError,
    AIMalformedResponseError,
    AIPermanentError,
    AIProviderUnavailableError,
    AIRateLimitError,
    AIStructuredOutputValidationError,
    AITimeoutError,
    AIToolNotAllowedError,
    AITransientError,
    AIUnsupportedCapabilityError,
)
from app.ai.gateway import AIGateway
from app.ai.schemas import (
    ChatMessage,
    GenerationResponse,
    MessageRole,
    ToolCall,
    ToolCategory,
    ToolDefinition,
)
from app.ai.tools import ToolRegistry

__all__ = [
    "AIGateway",
    "AIGatewayError",
    "AIConfigError",
    "AIAuthenticationError",
    "AIUnsupportedCapabilityError",
    "AIToolNotAllowedError",
    "AIStructuredOutputValidationError",
    "AIMalformedResponseError",
    "AITransientError",
    "AIRateLimitError",
    "AITimeoutError",
    "AIProviderUnavailableError",
    "AIPermanentError",
    "ChatMessage",
    "GenerationResponse",
    "MessageRole",
    "ToolCall",
    "ToolCategory",
    "ToolDefinition",
    "ToolRegistry",
]
