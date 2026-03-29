"""Celery task package."""

from app.workers.tasks.crawl import run_crawl_job_task  # noqa: F401
from app.workers.tasks.ping import ping  # noqa: F401

__all__ = ["ping", "run_crawl_job_task"]
