"""
Quiz Service Celery Configuration (local)
Standalone Celery app setup for the quiz service.
"""

import os
import logging
from celery import Celery

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Use Redis URL from env (docker-compose provides REDIS_URL)
BROKER_URL = os.getenv("REDIS_URL", "redis://redis:6379/0")

celery_app = Celery(
    "quiz_service",
    broker=BROKER_URL,
    backend=BROKER_URL,
)

# Log configuration
logger.info(f"Celery app configured with broker URL: {BROKER_URL}")

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    # Fix for RPC errors
    task_always_eager=False,
    task_eager_propagates=True,
    worker_prefetch_multiplier=1,
    worker_max_tasks_per_child=1000,
    worker_max_memory_per_child=200000,  # 200MB
    # Redis connection settings
    broker_connection_retry_on_startup=True,
    broker_connection_retry=True,
    broker_connection_max_retries=10,
    # Result backend settings
    result_expires=3600,  # 1 hour
    result_persistent=False,
)

def quiz_task(func):
    """Decorator to register quiz tasks."""
    return celery_app.task(name=f"app.tasks.{func.__name__}")(func)

__all__ = ["celery_app", "quiz_task"]

# Import tasks to register them with celery
try:
    from . import tasks  # noqa: F401
    logger.info("Tasks imported successfully")
except Exception as e:
    logger.warning(f"Failed to import tasks: {e}")
    # Avoid hard import failures during tooling
    pass
