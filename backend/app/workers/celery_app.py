"""Celery application instance and worker integration."""

from __future__ import annotations

from celery import Celery
from celery.signals import worker_process_init

from app.core.settings import get_settings


def _build_celery() -> Celery:
    settings = get_settings()
    app = Celery(
        "university_chatbot",
        broker=settings.celery_broker_url,
        backend=settings.celery_result_backend,
    )
    app.conf.update(
        task_default_queue="default",
        task_serializer="json",
        result_serializer="json",
        accept_content=["json"],
        timezone="UTC",
        enable_utc=True,
        task_track_started=True,
        task_time_limit=60 * 60,
        task_soft_time_limit=int(60 * 60 * 0.9),
        broker_connection_retry_on_startup=True,
        result_expires=60 * 60 * 24,
    )
    return app


celery_app = _build_celery()


@worker_process_init.connect
def _configure_worker_logging(**_kwargs: object) -> None:
    """Align worker process logging with API structured logging."""
    from app.core.logging import configure_logging

    configure_logging()


import app.workers.tasks.crawl  # noqa: E402,F401 — register task
from app.workers.tasks import ping  # noqa: E402,F401
