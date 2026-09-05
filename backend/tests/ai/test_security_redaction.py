"""Tests for secret masking, token redaction, and logging security."""

from app.ai.guardrails.redaction import redact_secrets, sanitize_payload


def test_redact_razorpay_keys():
    """Verify live and test Razorpay key IDs are masked."""
    text = "Key: rzp_test_1DP5mmOlF5G5ag and live key rzp_live_5gN8uV2kLP9812"
    redacted = redact_secrets(text)
    assert "rzp_test_1DP5mmOlF5G5ag" not in redacted
    assert "rzp_live_5gN8uV2kLP9812" not in redacted
    assert "[REDACTED_RAZORPAY_KEY]" in redacted


def test_redact_openai_api_keys():
    """Verify OpenAI sk- API keys are masked."""
    text = "Authorization sk-proj-1234567890abcdef1234567890abcdef12345"
    redacted = redact_secrets(text)
    assert "sk-proj-1234567890abcdef" not in redacted
    assert "[REDACTED_API_KEY]" in redacted


def test_redact_credit_cards():
    """Verify 16-digit card numbers are masked."""
    text = "Customer card: 4111 2222 3333 4444 on file"
    redacted = redact_secrets(text)
    assert "4111 2222 3333 4444" not in redacted
    assert "[REDACTED_CARD_NUMBER]" in redacted


def test_sanitize_payload_nested_dict():
    """Verify nested dictionary secret fields are sanitized."""
    payload = {
        "user": "merchant_1",
        "api_key": "secret_key_value_12345",
        "nested": {
            "password": "super_secret_password",
            "token": "token_abc_xyz",
            "safe_field": "public_data",
        },
    }
    sanitized = sanitize_payload(payload)

    assert sanitized["user"] == "merchant_1"
    assert sanitized["api_key"] == "[REDACTED_SECRET]"
    assert sanitized["nested"]["password"] == "[REDACTED_SECRET]"
    assert sanitized["nested"]["token"] == "[REDACTED_SECRET]"
    assert sanitized["nested"]["safe_field"] == "public_data"
