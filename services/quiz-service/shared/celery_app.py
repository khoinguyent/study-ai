"""
Shared Celery Configuration for Study AI Platform
Provides Celery app configuration for background task processing
Updated to use infrastructure abstraction layer
"""

from celery import Celery
from .events import EventType, create_event
from .event_publisher import EventPublisher
from .infrastructure import infra_config, get_message_broker, get_task_queue, is_local_environment
import os
import logging

logger = logging.getLogger(__name__)

# Get configuration from infrastructure layer
CELERY_BROKER_URL = infra_config.get_message_broker_url()
CELERY_RESULT_BACKEND = infra_config.get_message_broker_url()

# Create Celery app
celery_app = Celery(
    'study_ai',
    broker=CELERY_BROKER_URL,
    backend=CELERY_BROKER_URL
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
    
    # Dead Letter Queue Configuration
    task_default_queue='default',
    task_default_exchange='default',
    task_default_routing_key='default',
    
    # Retry configuration
    task_acks_late=True,
    task_reject_on_worker_lost=True,
    
    # Simple queue configuration (temporarily disable DLQ for testing)
    task_queues={
        'document_queue': {
            'exchange': 'document_queue',
            'routing_key': 'document_queue',
        },
        'indexing_queue': {
            'exchange': 'indexing_queue',
            'routing_key': 'indexing_queue',
        },
        'quiz_queue': {
            'exchange': 'quiz_queue',
            'routing_key': 'quiz_queue',
        },
    },
    
    # Exchange configuration
    task_default_exchange_type='direct',
)

# Task routing
celery_app.conf.task_routes = {
    'app.tasks.*': {'queue': 'document_queue'},
    'app.indexing_tasks.*': {'queue': 'indexing_queue'},
    'app.quiz_tasks.*': {'queue': 'quiz_queue'},
    # More specific routing for indexing tasks
    'app.tasks.index_document': {'queue': 'indexing_queue'},
    'app.tasks.reindex_document': {'queue': 'indexing_queue'},
    'app.tasks.delete_document_index': {'queue': 'indexing_queue'},
}

# Event publisher for tasks
event_publisher = EventPublisher()

# Dead Letter Queue Handler
class DeadLetterQueueHandler:
    """Handler for processing dead letter queue messages"""
    
    def __init__(self):
        self.event_publisher = event_publisher
    
    def handle_dlq_message(self, task_id: str, task_name: str, error_message: str, 
                          original_queue: str, retry_count: int = 0):
        """Handle a message that has been moved to the dead letter queue"""
        logger = logging.getLogger(__name__)
        
        logger.error(f"Task {task_id} ({task_name}) moved to DLQ from {original_queue}. "
                    f"Error: {error_message}. Retry count: {retry_count}")
        
        # Publish DLQ event
        self.event_publisher.publish_dlq_event(
            task_id=task_id,
            task_name=task_name,
            error_message=error_message,
            original_queue=original_queue,
            retry_count=retry_count
        )
        
        # Send notification about failed task
        self.event_publisher.publish_user_notification(
            user_id="system",
            notification_type="dlq_alert",
            title="Task Processing Failed",
            message=f"Task {task_name} has failed and been moved to dead letter queue",
            priority="high",
            metadata={
                "task_id": task_id,
                "task_name": task_name,
                "error": error_message,
                "queue": original_queue,
                "retry_count": retry_count
            }
        )

# Global DLQ handler instance
dlq_handler = DeadLetterQueueHandler()

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
            status="started",
            progress=0,
            message="Task started"
        )
    
    def publish_task_progress(self, task_id: str, user_id: str, task_type: str, 
                            progress: int, message: str):
        """Publish task progress event"""
        self.event_publisher.publish_task_status_update(
            user_id=user_id,
            task_id=task_id,
            task_type=task_type,
            status="progress",
            progress=progress,
            message=message
        )
    
    def publish_task_completed(self, task_id: str, user_id: str, task_type: str, 
                             message: str):
        """Publish task completed event"""
        self.event_publisher.publish_task_status_update(
            user_id=user_id,
            task_id=task_id,
            task_type=task_type,
            status="completed",
            progress=100,
            message=message
        )
    
    def publish_task_failed(self, task_id: str, user_id: str, task_type: str, 
                          error_message: str):
        """Publish task failed event"""
        self.event_publisher.publish_task_status_update(
            user_id=user_id,
            task_id=task_id,
            task_type=task_type,
            status="failed",
            progress=0,
            message=f"Task failed: {error_message}"
        )

# Task decorators for different queues
def document_task(func):
    """Decorator for document processing tasks"""
    return celery_app.task(queue='document_queue')(func)

def indexing_task(func):
    """Decorator for indexing tasks"""
    return celery_app.task(queue='indexing_queue')(func)

def quiz_task(func):
    """Decorator for quiz generation tasks"""
    return celery_app.task(queue='quiz_queue')(func)

# Infrastructure-aware task enqueuing
def enqueue_task(task_name: str, args: tuple = None, kwargs: dict = None, 
                queue: str = 'default') -> str:
    """
    Enqueue a task using the appropriate infrastructure
    
    Args:
        task_name: Name of the task to execute
        args: Positional arguments for the task
        kwargs: Keyword arguments for the task
        queue: Queue name (for Celery) or queue URL (for SQS)
    
    Returns:
        Task ID or message ID
    """
    if is_local_environment():
        # Use Celery for local environment
        task = celery_app.send_task(task_name, args=args, kwargs=kwargs)
        return task.id
    else:
        # Use infrastructure abstraction for cloud environment
        task_queue = get_task_queue()
        if task_queue.connect():
            try:
                return task_queue.enqueue(task_name, args=args, kwargs=kwargs)
            finally:
                task_queue.disconnect()
        else:
            logger.error("Failed to connect to task queue")
            return ""

# Backward compatibility functions
def get_celery_app():
    """Get the Celery app instance (backward compatibility)"""
    return celery_app

def get_celery_broker_url():
    """Get the Celery broker URL (backward compatibility)"""
    return CELERY_BROKER_URL

def get_celery_result_backend():
    """Get the Celery result backend URL (backward compatibility)"""
    return CELERY_RESULT_BACKEND 