"""Shared API response models (Pydantic v2)."""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field


class ErrorDetail(BaseModel):
    """Machine-readable error body."""

    code: str = Field(..., description="Stable error code for clients")
    message: str = Field(..., description="Human-readable message")
    details: dict[str, Any] | None = Field(default=None, description="Optional structured detail")


class ErrorResponse(BaseModel):
    """Standard error envelope."""

    error: ErrorDetail


class Meta(BaseModel):
    """Optional metadata included on success responses (e.g. request correlation)."""

    request_id: str | None = None


class SuccessEnvelope(BaseModel):
    """Generic success wrapper for list/detail endpoints (use when helpful)."""

    data: Any
    meta: Meta | None = None


class ComponentHealth(BaseModel):
    """Single dependency check (database, redis, ...)."""

    name: str
    status: Literal["up", "down"]
    latency_ms: float | None = None
    error: str | None = None


class HealthCheckResponse(BaseModel):
    """Readiness-style health with dependency breakdown."""

    status: Literal["healthy", "degraded", "unhealthy"]
    version: str
    environment: str
    dependencies: list[ComponentHealth]


class LivenessResponse(BaseModel):
    """Minimal liveness probe (process is up)."""

    status: Literal["ok"] = "ok"
