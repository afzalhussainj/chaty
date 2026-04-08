"""ASGI application factory."""

from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from slowapi.errors import RateLimitExceeded
from slowapi.extension import _rate_limit_exceeded_handler
from slowapi.middleware import SlowAPIMiddleware

from app.api.exception_handlers import register_exception_handlers
from app.api.router import api_router
from app.core.lifespan import lifespan
from app.core.logging import configure_logging, get_logger
from app.core.rate_limit import public_limiter
from app.core.settings import get_settings
from app.middleware.request_context import RequestContextMiddleware
from app.schemas.common import LivenessResponse


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    configure_logging()
    log = get_logger(__name__)
    settings = get_settings()

    app = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        debug=settings.debug,
        lifespan=lifespan,
    )

    register_exception_handlers(app)

    app.state.limiter = public_limiter
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

    app.add_middleware(SlowAPIMiddleware)
    app.add_middleware(RequestContextMiddleware)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.get("/health", response_model=LivenessResponse, tags=["health"])
    def liveness() -> LivenessResponse:
        """Minimal liveness probe (process up); independent of DB/Redis."""
        return LivenessResponse()

    app.include_router(api_router, prefix="/api")

    log.info(
        "application_created",
        app_name=settings.app_name,
        version=settings.app_version,
        environment=settings.app_env,
    )

    return app


app = create_app()
