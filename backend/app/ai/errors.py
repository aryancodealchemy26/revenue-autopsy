class AIGatewayError(Exception):
    """Base class for all AI Gateway errors."""

    def __init__(self, message: str):
        super().__init__(message)
        self.message = message


class AIConfigError(AIGatewayError):
    """Invalid configuration (missing provider, model, or API key)."""


class AIAuthenticationError(AIGatewayError):
    """Authentication failed (e.g., 401 Unauthorized)."""


class AIUnsupportedCapabilityError(AIGatewayError):
    """Provider does not support a requested capability (structured output, tools)."""


class AIToolNotAllowedError(AIGatewayError):
    """Requested tool call is not in the allowlist or is disallowed (write‑capable)."""


class AIStructuredOutputValidationError(AIGatewayError):
    """Pydantic validation of the provider's structured output failed."""


class AIMalformedResponseError(AIGatewayError):
    """Provider returned malformed JSON when JSON was expected."""


class AITransientError(AIGatewayError):
    """Base class for retryable transient errors (rate‑limit, timeout, service unavailable)."""


class AIRateLimitError(AITransientError):
    """429 Too Many Requests or similar rate‑limit response."""


class AITimeoutError(AITransientError):
    """Operation timed out."""


class AIProviderUnavailableError(AITransientError):
    """502/503/504 service unavailable errors."""


class AIPermanentError(AIGatewayError):
    """Non‑retryable permanent error (bad request, content filtered, etc.)."""
