"""Celery task logging context (correlation IDs in structlog)."""

from __future__ import annotations

import structlog
from celery.signals import task_postrun, task_prerun


@task_prerun.connect
def bind_celery_task_context(
    task_id: str | None = None,
    task=None,
    **_kwargs: object,
) -> None:
    structlog.contextvars.bind_contextvars(
        celery_task_id=task_id,
        celery_task_name=getattr(task, "name", None) if task else None,
    )


@task_postrun.connect
def clear_celery_task_context(**_kwargs: object) -> None:
    structlog.contextvars.clear_contextvars()
