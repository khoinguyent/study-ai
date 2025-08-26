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

# Add error handling for broker connection
@celery_app.on_after_configure.connect
def setup_periodic_tasks(sender, **kwargs):
    """Setup periodic tasks and error handling"""
    logger.info("Celery app configured successfully")
    logger.info(f"Broker URL: {BROKER_URL}")

@celery_app.on_after_finalize.connect
def finalize_app(sender, **kwargs):
    """Finalize app configuration"""
    logger.info("Celery app finalized successfully")

@celery_app.on_worker_init.connect
def worker_init(sender, **kwargs):
    """Worker initialization"""
    logger.info("Celery worker initialized successfully")

@celery_app.on_worker_shutdown.connect
def worker_shutdown(sender, **kwargs):
    """Worker shutdown"""
    logger.info("Celery worker shutting down")

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
