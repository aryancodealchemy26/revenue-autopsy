"""Tests for application configuration and settings behavior."""

from pydantic import SecretStr

from app.core.config import Settings


def test_default_settings():
    """Verify application settings initialize cleanly with expected defaults."""
    settings = Settings()
    assert settings.APP_NAME == "Revenue Autopsy"
    assert settings.APP_ENV == "development"
    assert isinstance(settings.CORS_ORIGINS, list)
    assert len(settings.CORS_ORIGINS) > 0


def test_missing_optional_credentials_startup():
    """Verify missing optional integration credentials do not prevent startup."""
    settings = Settings(
        RAZORPAY_KEY_ID=None,
        RAZORPAY_KEY_SECRET=None,
        RAZORPAY_WEBHOOK_SECRET=None,
        LLM_PROVIDER=None,
        LLM_MODEL=None,
        LLM_API_KEY=None,
    )
    assert settings.RAZORPAY_KEY_ID is None
    assert settings.RAZORPAY_KEY_SECRET is None
    assert settings.LLM_API_KEY is None


def test_secrets_are_masked():
    """Verify secret credentials are using SecretStr to prevent raw logging."""
    settings = Settings(
        RAZORPAY_KEY_SECRET=SecretStr("super_secret_key"),
        LLM_API_KEY=SecretStr("sk-test-12345"),
    )
    assert repr(settings.RAZORPAY_KEY_SECRET) == "SecretStr('**********')"
    assert repr(settings.LLM_API_KEY) == "SecretStr('**********')"
    assert "super_secret_key" not in repr(settings.RAZORPAY_KEY_SECRET)
    assert "sk-test-12345" not in repr(settings.LLM_API_KEY)
