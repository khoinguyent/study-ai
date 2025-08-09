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
    
    # Dead Letter Queue Configuration
    task_default_queue='default',
    task_default_exchange='default',
    task_default_routing_key='default',
    
    # Retry configuration
    task_acks_late=True,
    task_reject_on_worker_lost=True,
    
    # Dead Letter Queue settings
    task_queues={
        'document_queue': {
            'exchange': 'document_queue',
            'routing_key': 'document_queue',
            'queue_arguments': {
                'x-dead-letter-exchange': 'dlq_exchange',
                'x-dead-letter-routing-key': 'dlq_document',
                'x-message-ttl': 300000,  # 5 minutes TTL
            }
        },
        'indexing_queue': {
            'exchange': 'indexing_queue',
            'routing_key': 'indexing_queue',
            'queue_arguments': {
                'x-dead-letter-exchange': 'dlq_exchange',
                'x-dead-letter-routing-key': 'dlq_indexing',
                'x-message-ttl': 300000,  # 5 minutes TTL
            }
        },
        'quiz_queue': {
            'exchange': 'quiz_queue',
            'routing_key': 'quiz_queue',
            'queue_arguments': {
                'x-dead-letter-exchange': 'dlq_exchange',
                'x-dead-letter-routing-key': 'dlq_quiz',
                'x-message-ttl': 300000,  # 5 minutes TTL
            }
        },
        'dlq_document': {
            'exchange': 'dlq_exchange',
            'routing_key': 'dlq_document',
        },
        'dlq_indexing': {
            'exchange': 'dlq_exchange',
            'routing_key': 'dlq_indexing',
        },
        'dlq_quiz': {
            'exchange': 'dlq_exchange',
            'routing_key': 'dlq_quiz',
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

# Task decorators with retry and DLQ support
def document_task(func):
    """Decorator for document processing tasks with retry and DLQ support"""
    return celery_app.task(
        bind=True, 
        queue='document_queue',
        max_retries=3,
        default_retry_delay=60,  # 1 minute
        autoretry_for=(Exception,),
        retry_backoff=True,
        retry_jitter=True
    )(func)

def indexing_task(func):
    """Decorator for indexing tasks with retry and DLQ support"""
    return celery_app.task(
        bind=True, 
        queue='indexing_queue',
        max_retries=3,
        default_retry_delay=60,  # 1 minute
        autoretry_for=(Exception,),
        retry_backoff=True,
        retry_jitter=True
    )(func)

def quiz_task(func):
    """Decorator for quiz generation tasks with retry and DLQ support"""
    return celery_app.task(
        bind=True, 
        queue='quiz_queue',
        max_retries=3,
        default_retry_delay=60,  # 1 minute
        autoretry_for=(Exception,),
        retry_backoff=True,
        retry_jitter=True
    )(func)

def dlq_task(func):
    """Decorator for dead letter queue processing tasks"""
    return celery_app.task(
        bind=True,
        queue='dlq_document',  # Default to document DLQ
        max_retries=0,  # No retries for DLQ tasks
    )(func) 