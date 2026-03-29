"""Readiness health endpoint (liveness is mounted at app root in main)."""

from __future__ import annotations

from fastapi import APIRouter
from fastapi.responses import JSONResponse

from app.services.health_service import build_health_check_response

router = APIRouter()


@router.get("/health")
def readiness() -> JSONResponse:
    """Dependency checks; returns 503 if any critical dependency is down."""
    body = build_health_check_response()
    code = 200 if body.status == "healthy" else 503
    return JSONResponse(status_code=code, content=body.model_dump())
