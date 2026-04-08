"""Map exceptions to standard JSON error responses."""

from __future__ import annotations

from fastapi import FastAPI, HTTPException, Request, status
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from app.core.exceptions import AppError
from app.core.logging import get_logger
from app.core.settings import get_settings
from app.schemas.common import ErrorDetail, ErrorResponse

logger = get_logger(__name__)


def register_exception_handlers(app: FastAPI) -> None:
    """Register handlers in most-specific-first order."""

    def _rid(request: Request) -> str | None:
        return getattr(request.state, "request_id", None)

    @app.exception_handler(AppError)
    async def app_error_handler(request: Request, exc: AppError) -> JSONResponse:
        return JSONResponse(
            status_code=exc.status_code,
            content=jsonable_encoder(
                ErrorResponse(
                    error=ErrorDetail(
                        code=exc.code,
                        message=exc.message,
                        details=exc.details or None,
                        request_id=_rid(request),
                    )
                ).model_dump(),
            ),
        )

    @app.exception_handler(HTTPException)
    async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
        detail = exc.detail
        message = detail if isinstance(detail, str) else "Request failed"
        return JSONResponse(
            status_code=exc.status_code,
            content=jsonable_encoder(
                ErrorResponse(
                    error=ErrorDetail(
                        code=f"http_{exc.status_code}",
                        message=message,
                        request_id=_rid(request),
                    )
                ).model_dump(),
            ),
        )

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(
        request: Request, exc: RequestValidationError
    ) -> JSONResponse:
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content=jsonable_encoder(
                ErrorResponse(
                    error=ErrorDetail(
                        code="validation_error",
                        message="Request validation failed",
                        details={"errors": exc.errors()},
                        request_id=_rid(request),
                    )
                ).model_dump(),
            ),
        )

    @app.exception_handler(Exception)
    async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
        logger.exception(
            "unhandled_exception",
            path=str(request.url.path),
            request_id=_rid(request),
        )
        settings = get_settings()
        message = str(exc) if settings.debug else "Internal server error"
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content=jsonable_encoder(
                ErrorResponse(
                    error=ErrorDetail(
                        code="internal_error",
                        message=message,
                        request_id=_rid(request),
                    ),
                ).model_dump(),
            ),
        )
