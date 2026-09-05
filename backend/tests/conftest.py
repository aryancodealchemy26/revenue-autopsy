"""Standard pytest configuration and fixtures for Revenue Autopsy test suite."""

import pytest


@pytest.fixture(scope="session")
def anyio_backend():
    """Force pytest-anyio to use the asyncio backend for all async tests."""
    return "asyncio"
