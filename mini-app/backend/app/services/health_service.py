"""Health checks for readiness probes (database, Redis)."""

from __future__ import annotations

import time
from typing import Literal

from sqlalchemy import text

from app.core.redis_client import get_redis
from app.core.settings import get_settings
from app.db.session import get_engine
from app.schemas.common import ComponentHealth, HealthCheckResponse


def check_celery_workers() -> ComponentHealth:
    """Best-effort: at least one Celery worker responds to inspect ping."""
    start = time.perf_counter()
    try:
        from app.workers.celery_app import celery_app

        insp = celery_app.control.inspect(timeout=1.5)
        if insp is None:
            return ComponentHealth(
                name="celery_workers",
                status="down",
                error="inspect handle unavailable (broker down?)",
            )
        ping = insp.ping()
        latency_ms = (time.perf_counter() - start) * 1000
        if ping:
            return ComponentHealth(
                name="celery_workers",
                status="up",
                latency_ms=round(latency_ms, 3),
            )
        return ComponentHealth(
            name="celery_workers",
            status="down",
            error="no workers replied to ping",
        )
    except Exception as exc:  # noqa: BLE001
        return ComponentHealth(name="celery_workers", status="down", error=str(exc))


def check_database() -> ComponentHealth:
    """Verify PostgreSQL connectivity."""
    start = time.perf_counter()
    try:
        with get_engine().connect() as conn:
            conn.execute(text("SELECT 1"))
        latency_ms = (time.perf_counter() - start) * 1000
        return ComponentHealth(
            name="database",
            status="up",
            latency_ms=round(latency_ms, 3),
        )
    except Exception as exc:  # noqa: BLE001 — surface cause to readiness response
        return ComponentHealth(name="database", status="down", error=str(exc))


def check_redis() -> ComponentHealth:
    """Verify Redis connectivity (PING)."""
    start = time.perf_counter()
    try:
        client = get_redis()
        client.ping()
        latency_ms = (time.perf_counter() - start) * 1000
        return ComponentHealth(
            name="redis",
            status="up",
            latency_ms=round(latency_ms, 3),
        )
    except Exception as exc:  # noqa: BLE001
        return ComponentHealth(name="redis", status="down", error=str(exc))


def build_health_check_response() -> HealthCheckResponse:
    """Aggregate dependency checks into a single readiness payload."""
    settings = get_settings()
    deps: list[ComponentHealth] = [check_database(), check_redis()]
    if settings.health_check_celery_workers:
        deps.append(check_celery_workers())

    critical = [d for d in deps if d.name in ("database", "redis")]
    critical_down = any(d.status == "down" for d in critical)
    worker = next((d for d in deps if d.name == "celery_workers"), None)
    worker_down = worker is not None and worker.status == "down"

    if critical_down:
        status: Literal["healthy", "degraded", "unhealthy"] = "unhealthy"
    elif worker_down:
        status = "degraded"
    else:
        status = "healthy"

    return HealthCheckResponse(
        status=status,
        version=settings.app_version,
        environment=settings.app_env,
        dependencies=deps,
    )
