"""Tests for merchant domain models and enums."""

from uuid import uuid4
import pytest
from pydantic import ValidationError

from app.domain.merchants.enums import MerchantStatus
from app.domain.merchants.models import Merchant


def test_merchant_creation_valid():
    """Test creating a valid Merchant entity containing only required fields."""
    merchant_id = uuid4()
    merchant = Merchant(
        merchant_id=merchant_id,
        name="Acme E-Commerce",
        currency="inr",
        timezone="Asia/Kolkata",
        status=MerchantStatus.ACTIVE,
    )
    assert merchant.merchant_id == merchant_id
    assert merchant.name == "Acme E-Commerce"
    assert merchant.currency == "INR"
    assert merchant.status == MerchantStatus.ACTIVE
    assert not hasattr(merchant, "created_at")
    assert not hasattr(merchant, "updated_at")


def test_merchant_invalid_currency_rejection():
    """Test invalid currency code rejection."""
    with pytest.raises(ValidationError):
        Merchant(
            name="Acme",
            currency="INVALID",
        )
