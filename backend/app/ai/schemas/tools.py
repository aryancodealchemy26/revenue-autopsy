"""AI tool schemas used for validation and allowlisting.

The gateway validates any tool-calls emitted by the model against these
schemas but never executes them.
"""
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field


class ToolCategory(str, Enum):
    READ_ONLY = "read_only"
    WRITE_CAPABLE = "write_capable"


class ToolDefinition(BaseModel):
    name: str = Field(..., description="Unique tool identifier")
    description: str = Field(..., description="Human‑readable description")
    category: ToolCategory = Field(..., description="Category of the tool")
    parameters_schema: Dict[str, Any] = Field(
        ..., description="JSON‑Schema describing the tool's arguments"
    )
    is_financial_write: bool = Field(
        False,
        description="True if the tool performs a financial write; such tools are disallowed in Phase 9.",
    )


class ToolCall(BaseModel):
    """Validated tool call data returned by the gateway.

    The gateway does **not** execute the call – it merely validates the
    request and returns the structured data for downstream orchestration.
    """
    model_config = ConfigDict(frozen=True)

    tool_name: str = Field(..., description="Name of the requested tool")
    arguments: Dict[str, Any] = Field(..., description="Validated arguments for the tool")
    call_id: Optional[str] = Field(
        None, description="Optional identifier linking the call to the LLM response"
    )
