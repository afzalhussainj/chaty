"""Request-scoped context (correlation / request ID for logs and responses)."""

from __future__ import annotations

import uuid

import structlog
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response


class RequestContextMiddleware(BaseHTTPMiddleware):
    """Bind `request_id` for structlog and echo `X-Request-ID` on the response."""

    async def dispatch(self, request: Request, call_next) -> Response:
        header_rid = request.headers.get("X-Request-ID")
        header_cid = request.headers.get("X-Correlation-ID")
        request_id = header_rid or header_cid or str(uuid.uuid4())
        structlog.contextvars.bind_contextvars(request_id=request_id)
        request.state.request_id = request_id
        try:
            response = await call_next(request)
            response.headers["X-Request-ID"] = request_id
            response.headers["X-Correlation-ID"] = request_id
            return response
        finally:
            structlog.contextvars.clear_contextvars()
