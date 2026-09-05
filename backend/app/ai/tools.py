"""Tool registry and validation utilities for the AI Gateway.

The registry holds the allowed tool definitions for the current request. The
gateway uses it to validate any tool‑call objects returned by the LLM before
handing them off to downstream policy/executor layers.
"""

import logging
from typing import Dict, List, Optional

from app.ai.errors import AIToolNotAllowedError
from app.ai.schemas.tools import ToolDefinition, ToolCall

logger = logging.getLogger(__name__)


class ToolRegistry:
    """Manage a collection of :class:`ToolDefinition` objects.

    In Phase 9 we keep the registry simple – definitions can be added manually
    (e.g., during application start‑up) or loaded from a static module. For the
    test suite the registry is expected to contain at least one dummy read‑only
    tool so that ``allowed_tools`` validation can exercise the code path.
    """

    def __init__(self, initial_tools: Optional[List[ToolDefinition]] = None):
        self._tools: Dict[str, ToolDefinition] = {}
        if initial_tools:
            for td in initial_tools:
                self.register(td)
        logger.debug("ToolRegistry initialized with %d tools", len(self._tools))

    # ---------------------------------------------------------------------
    # Registry management
    # ---------------------------------------------------------------------
    def register(self, tool_def: ToolDefinition) -> None:
        """Add a new tool definition to the registry.

        If a tool with the same name already exists it will be overwritten – the
        registry is not expected to be mutated at runtime in production, but the
        behaviour is convenient for tests.
        """
        self._tools[tool_def.name] = tool_def
        logger.debug("Registered tool %s (category=%s)", tool_def.name, tool_def.category)

    def get_definitions(self) -> List[ToolDefinition]:
        """Return a list of all registered ``ToolDefinition`` objects.
        """
        return list(self._tools.values())

    def lookup(self, name: str) -> Optional[ToolDefinition]:
        return self._tools.get(name)

    # ---------------------------------------------------------------------
    # Validation
    # ---------------------------------------------------------------------
    def validate_call(self, tool_call: ToolCall, allowed_tools: List[str]) -> None:
        """Validate a ``ToolCall`` against the registry and an allow‑list.

        Raises
        ------
        AIToolNotAllowedError
            If the tool name is not registered or not present in ``allowed_tools``
            or if the tool is marked as ``WRITE_CAPABLE`` (financial write) – the
            gateway never permits write‑capable tools in Phase 9.
        """
        td = self.lookup(tool_call.tool_name)
        if td is None:
            raise AIToolNotAllowedError(f"Tool '{tool_call.tool_name}' is not registered")
        if tool_call.tool_name not in allowed_tools:
            raise AIToolNotAllowedError(
                f"Tool '{tool_call.tool_name}' is not in the allowed list for this request"
            )
        if td.is_financial_write:
            raise AIToolNotAllowedError(
                f"Tool '{tool_call.tool_name}' is a financial‑write capability and is disallowed"
            )
        # Additional schema validation could be added here (e.g., using jsonschema)
        logger.debug("Tool call %s validated successfully", tool_call.tool_name)
