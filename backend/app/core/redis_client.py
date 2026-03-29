"""Redis connection management (sync client with connection pool)."""

from __future__ import annotations

import redis

from app.core.settings import get_settings

_client: redis.Redis | None = None


def get_redis() -> redis.Redis:
    """Return a singleton Redis client (lazy, uses connection pool internally)."""
    global _client
    if _client is None:
        settings = get_settings()
        _client = redis.Redis.from_url(settings.redis_url, decode_responses=True)
    return _client


def close_redis_pool() -> None:
    """Disconnect the client's pool (application shutdown and tests)."""
    global _client
    if _client is not None:
        _client.connection_pool.disconnect()
        _client = None


def reset_redis_client_for_tests() -> None:
    """Close client and clear singleton (tests only)."""
    close_redis_pool()
