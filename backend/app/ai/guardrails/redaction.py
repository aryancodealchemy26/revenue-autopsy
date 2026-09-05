"""Security guardrails for secret and sensitive credential redaction."""

import re
from typing import Any, Dict, List, Union

# Compiled regular expressions for sensitive patterns
PATTERNS = [
    # Razorpay Keys (live/test)
    (re.compile(r"rzp_(?:live|test)_[0-9a-zA-Z]{14,}", re.IGNORECASE), "[REDACTED_RAZORPAY_KEY]"),
    # OpenAI and standard Bearer / sk- API keys
    (re.compile(r"sk-[a-zA-Z0-9_\-]{20,}", re.IGNORECASE), "[REDACTED_API_KEY]"),
    (re.compile(r"(?i)(bearer\s+)[a-zA-Z0-9_\-\.]{20,}"), r"\1[REDACTED_TOKEN]"),
    # Credit / Debit Card numbers (13-19 digits with optional hyphens/spaces)
    (re.compile(r"\b(?:\d[ -]*?){13,19}\b"), "[REDACTED_CARD_NUMBER]"),
    # JSON / Header sensitive keys (password, api_key, secret, token, authorization)
    (
        re.compile(
            r"""(?i)(["']?(?:password|api_key|secret|token|auth_token|authorization|private_key)["']?\s*[:=]\s*["']?)([^"',\s\}]+)"""
        ),
        r"\1[REDACTED_SECRET]",
    ),
]


def redact_secrets(text: str) -> str:
    """Mask known sensitive patterns, API keys, and credentials from a string."""
    if not isinstance(text, str):
        return text

    sanitized = text
    for pattern, replacement in PATTERNS:
        sanitized = pattern.sub(replacement, sanitized)
    return sanitized


def sanitize_payload(payload: Any) -> Any:
    """Recursively sanitize strings, dictionaries, lists, or nested objects."""
    if isinstance(payload, str):
        return redact_secrets(payload)
    elif isinstance(payload, dict):
        sanitized_dict = {}
        for k, v in payload.items():
            # If the key itself is explicitly sensitive, mask value entirely
            if any(s in k.lower() for s in ["password", "secret", "api_key", "auth_token", "token", "authorization"]):
                sanitized_dict[k] = "[REDACTED_SECRET]"
            else:
                sanitized_dict[k] = sanitize_payload(v)
        return sanitized_dict
    elif isinstance(payload, (list, tuple, set)):
        return [sanitize_payload(item) for item in payload]
    return payload
