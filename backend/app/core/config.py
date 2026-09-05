"""Typed Application Configuration."""

from typing import List, Optional
from pydantic import SecretStr, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Centralized application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=True,
    )

    # Core Application Settings
    APP_ENV: str = "development"
    APP_NAME: str = "Revenue Autopsy"
    DEBUG: bool = False

    # CORS Settings (sensible default for dev, configurable via env string or list)
    CORS_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://localhost:5173",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:5173",
    ]

    # Database Settings (Optional in foundation phase)
    DATABASE_URL: Optional[SecretStr] = None
    DB_POOL_SIZE: int = 10
    DB_MAX_OVERFLOW: int = 20
    DB_ECHO: bool = False

    # Razorpay Credentials (Optional in foundation phase)
    RAZORPAY_KEY_ID: Optional[str] = None
    RAZORPAY_KEY_SECRET: Optional[SecretStr] = None
    RAZORPAY_WEBHOOK_SECRET: Optional[SecretStr] = None

    # LLM Settings (Optional in foundation phase)
    LLM_PROVIDER: Optional[str] = None
    LLM_MODEL: Optional[str] = None
    LLM_API_KEY: Optional[SecretStr] = None

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def assemble_cors_origins(cls, v: object) -> List[str]:
        if isinstance(v, str):
            return [i.strip() for i in v.split(",") if i.strip()]
        if isinstance(v, list):
            return [str(i) for i in v]
        return [
            "http://localhost:3000",
            "http://localhost:5173",
            "http://127.0.0.1:3000",
            "http://127.0.0.1:5173",
        ]


settings = Settings()
