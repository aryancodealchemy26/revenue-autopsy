"""Pydantic schemas for Chronological Incident Provenance & Audit Trail."""

from datetime import datetime
from pydantic import BaseModel, ConfigDict


class ProvenanceEventResponse(BaseModel):
    """API response schema for a chronological incident lifecycle transition event."""

    model_config = ConfigDict(from_attributes=True)

    step: str
    actor: str
    timestamp: datetime
    status: str
    summary: str
