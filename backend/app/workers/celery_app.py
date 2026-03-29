"""Celery application instance."""

from celery import Celery

from app.core.config import settings

celery_app = Celery("university_chatbot")
celery_app.conf.broker_url = settings.celery_broker_url
celery_app.conf.result_backend = settings.celery_result_backend
celery_app.conf.task_default_queue = "default"

# Import task modules for registration (after celery_app is defined).
from app.workers.tasks import ping  # noqa: E402,F401
