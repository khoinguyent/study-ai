"""
Shared Celery Configuration for Study AI Platform
Provides Celery app configuration for background task processing
"""

from celery import Celery
from .events import EventType, create_event
from .event_publisher import EventPublisher
import os

# Celery configuration
CELERY_BROKER_URL = os.getenv('REDIS_URL', 'redis://localhost:6379/0')
CELERY_RESULT_BACKEND = os.getenv('REDIS_URL', 'redis://localhost:6379/0')

# Create Celery app
celery_app = Celery(
    'study_ai',
    broker=CELERY_BROKER_URL,
    backend=CELERY_RESULT_BACKEND
)

# Celery configuration
celery_app.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,
    task_track_started=True,
    task_time_limit=30 * 60,  # 30 minutes
    task_soft_time_limit=25 * 60,  # 25 minutes
    worker_prefetch_multiplier=1,
    worker_max_tasks_per_child=1000,
    broker_connection_retry_on_startup=True,
)

# Task routing
celery_app.conf.task_routes = {
    'app.tasks.*': {'queue': 'document_queue'},
    'app.indexing_tasks.*': {'queue': 'indexing_queue'},
    'app.quiz_tasks.*': {'queue': 'quiz_queue'},
}

# Event publisher for tasks
event_publisher = EventPublisher()

# Task base class with event publishing
class EventDrivenTask:
    """Base class for tasks that publish events"""
    
    def __init__(self):
        self.event_publisher = event_publisher
    
    def publish_task_started(self, task_id: str, user_id: str, task_type: str):
        """Publish task started event"""
        self.event_publisher.publish_task_status_update(
            user_id=user_id,
            task_id=task_id,
            task_type=task_type,
            status="processing",
            progress=0,
            message="Task started"
        )
    
    def publish_task_progress(self, task_id: str, user_id: str, task_type: str, progress: int, message: str = None):
        """Publish task progress event"""
        self.event_publisher.publish_task_status_update(
            user_id=user_id,
            task_id=task_id,
            task_type=task_type,
            status="processing",
            progress=progress,
            message=message
        )
    
    def publish_task_completed(self, task_id: str, user_id: str, task_type: str, message: str = "Task completed"):
        """Publish task completed event"""
        self.event_publisher.publish_task_status_update(
            user_id=user_id,
            task_id=task_id,
            task_type=task_type,
            status="completed",
            progress=100,
            message=message
        )
    
    def publish_task_failed(self, task_id: str, user_id: str, task_type: str, error_message: str):
        """Publish task failed event"""
        self.event_publisher.publish_task_status_update(
            user_id=user_id,
            task_id=task_id,
            task_type=task_type,
            status="failed",
            progress=0,
            message=error_message
        )

# Task decorators
def document_task(func):
    """Decorator for document processing tasks"""
    return celery_app.task(bind=True, queue='document_queue')(func)

def indexing_task(func):
    """Decorator for indexing tasks"""
    return celery_app.task(bind=True, queue='indexing_queue')(func)

def quiz_task(func):
    """Decorator for quiz generation tasks"""
    return celery_app.task(bind=True, queue='quiz_queue')(func) 