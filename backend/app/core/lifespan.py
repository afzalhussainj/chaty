"""Application lifespan (startup / shutdown hooks)."""

from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.core.logging import get_logger
from app.core.redis_client import close_redis_pool
from app.db.session import dispose_engine


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncIterator[None]:
    """Release resources on shutdown (DB pool, Redis pool)."""
    logger = get_logger(__name__)
    logger.info("lifespan_enter")
    yield
    logger.info("lifespan_exit")
    dispose_engine()
    close_redis_pool()
