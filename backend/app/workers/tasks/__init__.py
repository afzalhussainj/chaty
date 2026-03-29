"""Celery task package."""

from app.workers.tasks.ping import ping  # noqa: F401

__all__ = ["ping"]
