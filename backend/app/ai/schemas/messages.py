"""AI message and response schemas used by the gateway.

These are deliberately lightweight to keep the AI layer independent of any
application‑specific models.
"""
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field


class MessageRole(str, Enum):
    system = "system"
    user = "user"
    assistant = "assistant"


class ChatMessage(BaseModel):
    model_config = ConfigDict(frozen=True)

    role: MessageRole = Field(..., description="The role of the message sender")
    content: str = Field(..., description="Raw message content")


class GenerationResponse(BaseModel):
    """Result of a text generation call.

    *content* holds the raw model output (or tool call JSON).
    *usage* is an optional dict mirroring OpenAI usage fields when available.
    """

    content: str
    usage: Optional[Dict[str, Any]] = None
    tool_calls: Optional[List[Dict[str, Any]]] = None
