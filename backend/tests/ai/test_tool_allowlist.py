"""Tests for tool metadata definition, allowlisting, and write-capable rejection."""

import pytest

from app.ai.errors import AIToolNotAllowedError
from app.ai.gateway import AIGateway
from app.ai.providers.fake_provider import FakeProvider
from app.ai.schemas.messages import ChatMessage, MessageRole
from app.ai.schemas.tools import ToolCategory, ToolDefinition
from app.ai.tools import ToolRegistry


def create_sample_registry() -> ToolRegistry:
    registry = ToolRegistry()
    registry.register(
        ToolDefinition(
            name="fetch_payment_analytics",
            description="Fetch read-only payment analytics",
            category=ToolCategory.READ_ONLY,
            parameters_schema={"type": "object", "properties": {"merchant_id": {"type": "string"}}},
            is_financial_write=False,
        )
    )
    registry.register(
        ToolDefinition(
            name="trigger_refund",
            description="Execute payment refund",
            category=ToolCategory.WRITE_CAPABLE,
            parameters_schema={"type": "object", "properties": {"payment_id": {"type": "string"}}},
            is_financial_write=True,
        )
    )
    return registry


@pytest.mark.anyio
async def test_tool_call_allowed_read_only_success():
    """Verify read-only registered tool in allowlist is validated and returned as ToolCall."""
    provider = FakeProvider()
    provider.canned_tool_calls = [
        {
            "id": "call_001",
            "name": "fetch_payment_analytics",
            "arguments": {"merchant_id": "merch_123"},
        }
    ]
    registry = create_sample_registry()
    gateway = AIGateway(provider=provider, default_model="gpt-4o-mini", tool_registry=registry)

    messages = [ChatMessage(role=MessageRole.user, content="Fetch analytics")]
    response = await gateway.generate(
        messages=messages,
        allowed_tools=["fetch_payment_analytics"],
    )

    assert response.tool_calls is not None
    assert len(response.tool_calls) == 1
    tool_call = response.tool_calls[0]
    assert tool_call.tool_name == "fetch_payment_analytics"
    assert tool_call.arguments == {"merchant_id": "merch_123"}
    assert tool_call.call_id == "call_001"


@pytest.mark.anyio
async def test_tool_call_unregistered_raises():
    """Verify model returning unregistered tool raises AIToolNotAllowedError."""
    provider = FakeProvider()
    provider.canned_tool_calls = [
        {
            "id": "call_002",
            "name": "unregistered_tool",
            "arguments": {},
        }
    ]
    registry = create_sample_registry()
    gateway = AIGateway(provider=provider, default_model="gpt-4o-mini", tool_registry=registry)

    messages = [ChatMessage(role=MessageRole.user, content="Do something")]
    with pytest.raises(AIToolNotAllowedError) as exc_info:
        await gateway.generate(messages=messages, allowed_tools=["fetch_payment_analytics"])
    assert "not registered" in str(exc_info.value)


@pytest.mark.anyio
async def test_tool_call_not_in_request_allowlist_raises():
    """Verify tool in registry but not in request allowed_tools is rejected."""
    provider = FakeProvider()
    provider.canned_tool_calls = [
        {
            "id": "call_003",
            "name": "fetch_payment_analytics",
            "arguments": {"merchant_id": "merch_123"},
        }
    ]
    registry = create_sample_registry()
    gateway = AIGateway(provider=provider, default_model="gpt-4o-mini", tool_registry=registry)

    messages = [ChatMessage(role=MessageRole.user, content="Fetch analytics")]
    with pytest.raises(AIToolNotAllowedError) as exc_info:
        await gateway.generate(messages=messages, allowed_tools=["some_other_tool"])
    assert "not in the allowed list" in str(exc_info.value)


@pytest.mark.anyio
async def test_tool_call_financial_write_disallowed_raises():
    """Verify write-capable tool (financial write) is rejected by Phase 9 AI Gateway."""
    provider = FakeProvider()
    provider.canned_tool_calls = [
        {
            "id": "call_004",
            "name": "trigger_refund",
            "arguments": {"payment_id": "pay_123"},
        }
    ]
    registry = create_sample_registry()
    gateway = AIGateway(provider=provider, default_model="gpt-4o-mini", tool_registry=registry)

    messages = [ChatMessage(role=MessageRole.user, content="Refund payment")]
    with pytest.raises(AIToolNotAllowedError) as exc_info:
        await gateway.generate(messages=messages, allowed_tools=["trigger_refund"])
    assert "financial" in str(exc_info.value) or "disallowed" in str(exc_info.value)
