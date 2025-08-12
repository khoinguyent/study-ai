"""
Quiz Service Celery Configuration (local)
Standalone Celery app setup for the quiz service.
"""

import os
from celery import Celery

# Use Redis URL from env (docker-compose provides REDIS_URL)
BROKER_URL = os.getenv("REDIS_URL", "redis://redis:6379/0")

celery_app = Celery(
    "quiz_service",
    broker=BROKER_URL,
    backend=BROKER_URL,
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
)

def quiz_task(func):
    """Decorator to register quiz tasks."""
    return celery_app.task(name=f"app.tasks.{func.__name__}")(func)

__all__ = ["celery_app", "quiz_task"]

# Import tasks to register them with celery
try:
    from . import tasks  # noqa: F401
except Exception:
    # Avoid hard import failures during tooling
    pass
