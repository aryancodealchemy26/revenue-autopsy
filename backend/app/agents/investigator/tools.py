"""Read-only diagnostic tool definitions for the Investigator Agent."""

from typing import List

from app.ai.schemas.tools import ToolCategory, ToolDefinition
from app.ai.tools import ToolRegistry

# Standard read-only diagnostic tool definitions
READ_ONLY_DIAGNOSTIC_TOOLS: List[ToolDefinition] = [
    ToolDefinition(
        name="get_payment_failure_breakdown",
        description="Fetch aggregated payment failure codes, route errors, and decline categories for a merchant.",
        category=ToolCategory.READ_ONLY,
        parameters_schema={
            "type": "object",
            "properties": {
                "merchant_id": {"type": "string", "description": "Target merchant UUID"},
                "window_minutes": {"type": "integer", "description": "Lookback window in minutes", "default": 60},
            },
            "required": ["merchant_id"],
        },
        is_financial_write=False,
    ),
    ToolDefinition(
        name="get_gateway_latency_metrics",
        description="Fetch p50, p95, and p99 latency percentiles for payment gateway routes.",
        category=ToolCategory.READ_ONLY,
        parameters_schema={
            "type": "object",
            "properties": {
                "route_name": {"type": "string", "description": "Payment route or bank identifier"},
            },
            "required": ["route_name"],
        },
        is_financial_write=False,
    ),
    ToolDefinition(
        name="get_webhook_delivery_status",
        description="Inspect merchant webhook dispatcher delivery success rates and retry queue sizes.",
        category=ToolCategory.READ_ONLY,
        parameters_schema={
            "type": "object",
            "properties": {
                "merchant_id": {"type": "string", "description": "Target merchant UUID"},
            },
            "required": ["merchant_id"],
        },
        is_financial_write=False,
    ),
]


def create_investigator_tool_registry() -> ToolRegistry:
    """Instantiate and return a ToolRegistry populated with read-only diagnostic tools."""
    registry = ToolRegistry()
    for tool_def in READ_ONLY_DIAGNOSTIC_TOOLS:
        registry.register(tool_def)
    return registry
