"""Pytest configuration and shared fixtures."""

from __future__ import annotations

import os

import pytest
from fastapi.testclient import TestClient

# Default test environment before application imports
os.environ.setdefault("APP_ENV", "test")

from app.core.redis_client import reset_redis_client_for_tests  # noqa: E402
from app.core.settings import get_settings  # noqa: E402
from app.db.session import reset_engine_for_tests  # noqa: E402
from app.main import create_app  # noqa: E402


@pytest.fixture
def app():
    """Fresh ASGI app instance per test."""
    return create_app()


@pytest.fixture
def client(app):
    """HTTP client with lifespan (startup/shutdown hooks)."""
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture
def clear_settings_cache():
    """Clear cached settings after a test that mutates environment."""
    yield
    get_settings.cache_clear()
    reset_engine_for_tests()
    reset_redis_client_for_tests()
