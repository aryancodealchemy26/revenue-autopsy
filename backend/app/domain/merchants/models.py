"""Merchant domain models."""

from uuid import UUID, uuid4
from pydantic import BaseModel, Field, field_validator

from app.domain.merchants.enums import MerchantStatus
from app.domain.shared import validate_currency_code


class Merchant(BaseModel):
    """Merchant entity representing an onboarded business or enterprise."""

    merchant_id: UUID = Field(default_factory=uuid4)
    name: str = Field(..., min_length=1, max_length=255)
    currency: str = Field(default="INR")
    timezone: str = Field(default="Asia/Kolkata")
    status: MerchantStatus = Field(default=MerchantStatus.ACTIVE)

    @field_validator("currency", mode="after")
    @classmethod
    def check_currency(cls, v: str) -> str:
        return validate_currency_code(v)
