"""Application-specific exceptions (map to HTTP responses via handlers)."""


class AppError(Exception):
    """Base error with stable `code` and HTTP status for API clients."""

    def __init__(
        self,
        message: str,
        *,
        code: str = "error",
        status_code: int = 500,
        details: dict[str, object] | None = None,
    ) -> None:
        super().__init__(message)
        self.message = message
        self.code = code
        self.status_code = status_code
        self.details = details or {}


class NotFoundError(AppError):
    def __init__(self, message: str = "Resource not found", *, code: str = "not_found") -> None:
        super().__init__(message, code=code, status_code=404)


class ValidationAppError(AppError):
    def __init__(
        self,
        message: str,
        *,
        code: str = "validation_error",
        details: dict[str, object] | None = None,
    ) -> None:
        super().__init__(message, code=code, status_code=422, details=details)


class ConflictError(AppError):
    def __init__(self, message: str, *, code: str = "conflict") -> None:
        super().__init__(message, code=code, status_code=409)


class UnauthorizedError(AppError):
    def __init__(self, message: str = "Unauthorized", *, code: str = "unauthorized") -> None:
        super().__init__(message, code=code, status_code=401)


class ForbiddenError(AppError):
    def __init__(self, message: str = "Forbidden", *, code: str = "forbidden") -> None:
        super().__init__(message, code=code, status_code=403)
