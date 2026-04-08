"""Readiness health endpoint (liveness is mounted at app root in main)."""

from __future__ import annotations

from fastapi import APIRouter
from fastapi.responses import JSONResponse

from app.services.health_service import build_health_check_response

router = APIRouter()


@router.get("/health")
def readiness() -> JSONResponse:
    """Dependency checks; 503 only when database or Redis is down (critical)."""
    body = build_health_check_response()
    code = 200 if body.status in ("healthy", "degraded") else 503
    return JSONResponse(status_code=code, content=body.model_dump())
