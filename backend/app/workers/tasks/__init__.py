"""Celery task package."""

from app.workers.tasks.crawl import run_crawl_job_task  # noqa: F401
from app.workers.tasks.extract import extract_html_source_task  # noqa: F401
from app.workers.tasks.ping import ping  # noqa: F401

__all__ = ["extract_html_source_task", "ping", "run_crawl_job_task"]
