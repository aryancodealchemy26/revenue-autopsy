"""Tenant authentication and context dependencies."""

from typing import Optional
from uuid import UUID
from fastapi import Header, HTTPException, status


async def get_current_merchant_id(
    x_merchant_id: Optional[str] = Header(None, alias="X-Merchant-ID"),
) -> UUID:
    """Extract and validate tenant merchant identity from request context.

    Treats X-Merchant-ID as tenant context in dev/sandbox.
    Rejects malformed or missing merchant context.
    Compatible with future JWT principal extraction.
    """
    if not x_merchant_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Missing required tenant header 'X-Merchant-ID'.",
        )
    try:
        return UUID(x_merchant_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Invalid UUID format for 'X-Merchant-ID': '{x_merchant_id}'.",
        )
