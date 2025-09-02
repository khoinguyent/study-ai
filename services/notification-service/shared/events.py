"""
Shared Events Module for Study AI Platform
Defines all event types and schemas for event-driven communication between services
"""

from enum import Enum
from typing import Dict, Any, Optional
from pydantic import BaseModel
from datetime import datetime
import uuid

class EventType(str, Enum):
    # Document Events
    DOCUMENT_UPLOADED = "document.uploaded"
    DOCUMENT_PROCESSING = "document.processing"
    DOCUMENT_PROCESSED = "document.processed"
    DOCUMENT_FAILED = "document.failed"
    
    # Indexing Events
    INDEXING_STARTED = "indexing.started"
    INDEXING_PROGRESS = "indexing.progress"
    INDEXING_COMPLETED = "indexing.completed"
    INDEXING_FAILED = "indexing.failed"
    
    # Quiz Events
    QUIZ_GENERATION_STARTED = "quiz.generation.started"
    QUIZ_GENERATION_PROGRESS = "quiz.generation.progress"
    QUIZ_GENERATED = "quiz.generated"
    QUIZ_GENERATION_FAILED = "quiz.generation.failed"
    
    # System Events
    TASK_STATUS_UPDATE = "task.status.update"
    USER_NOTIFICATION = "user.notification"
    
    # Dead Letter Queue Events
    DLQ_MESSAGE = "dlq.message"
    DLQ_PROCESSED = "dlq.processed"

class TaskStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

class BaseEvent(BaseModel):
    """Base event class with common fields"""
    event_id: str = None
    event_type: EventType
    timestamp: datetime = None
    user_id: str
    service_name: str
    metadata: Dict[str, Any] = {}
    
    def __init__(self, **data):
        super().__init__(**data)
        if not self.event_id:
            self.event_id = str(uuid.uuid4())
        if not self.timestamp:
            self.timestamp = datetime.utcnow()

class DocumentUploadedEvent(BaseEvent):
    """Event published when a document is uploaded"""
    document_id: str
    filename: str
    file_size: int
    content_type: str

class DocumentProcessingEvent(BaseEvent):
    """Event published when document processing starts"""
    document_id: str
    progress: int = 0

class DocumentProcessedEvent(BaseEvent):
    """Event published when document processing completes"""
    document_id: str
    chunks_count: int
    processing_time: float

class DocumentFailedEvent(BaseEvent):
    """Event published when document processing fails"""
    document_id: str
    error_message: str

class IndexingStartedEvent(BaseEvent):
    """Event published when indexing starts"""
    document_id: str
    chunks_count: int

class IndexingProgressEvent(BaseEvent):
    """Event published during indexing progress"""
    document_id: str
    progress: int
    processed_chunks: int
    total_chunks: int

class IndexingCompletedEvent(BaseEvent):
    """Event published when indexing completes"""
    document_id: str
    vectors_count: int
    indexing_time: float

class IndexingFailedEvent(BaseEvent):
    """Event published when indexing fails"""
    document_id: str
    error_message: str

class QuizGenerationStartedEvent(BaseEvent):
    """Event published when quiz generation starts"""
    quiz_id: str
    topic: str
    difficulty: str
    num_questions: int

class QuizGenerationProgressEvent(BaseEvent):
    """Event published during quiz generation progress"""
    quiz_id: str
    progress: int
    questions_generated: int
    total_questions: int

class QuizGeneratedEvent(BaseEvent):
    """Event published when quiz generation completes"""
    quiz_id: str
    questions_count: int
    generation_time: float

class QuizGenerationFailedEvent(BaseEvent):
    """Event published when quiz generation fails"""
    quiz_id: str
    error_message: str

class TaskStatusUpdateEvent(BaseEvent):
    """Event for general task status updates"""
    task_id: str
    task_type: str
    status: TaskStatus
    progress: int = 0
    message: Optional[str] = None

class UserNotificationEvent(BaseEvent):
    """Event for user notifications"""
    notification_type: str
    title: str
    message: str
    priority: str = "normal"  # low, normal, high, urgent

class DLQMessageEvent(BaseEvent):
    """Event published when a message is moved to dead letter queue"""
    task_id: str
    task_name: str
    error_message: str
    original_queue: str
    retry_count: int = 0
    original_args: Optional[Dict[str, Any]] = None
    original_kwargs: Optional[Dict[str, Any]] = None

class DLQProcessedEvent(BaseEvent):
    """Event published when a DLQ message is processed"""
    task_id: str
    task_name: str
    processing_result: str  # "retried", "discarded", "manual_review"
    processing_notes: Optional[str] = None

# Event factory function
def create_event(event_type: EventType, **kwargs) -> BaseEvent:
    """Factory function to create events based on type"""
    event_classes = {
        EventType.DOCUMENT_UPLOADED: DocumentUploadedEvent,
        EventType.DOCUMENT_PROCESSING: DocumentProcessingEvent,
        EventType.DOCUMENT_PROCESSED: DocumentProcessedEvent,
        EventType.DOCUMENT_FAILED: DocumentFailedEvent,
        EventType.INDEXING_STARTED: IndexingStartedEvent,
        EventType.INDEXING_PROGRESS: IndexingProgressEvent,
        EventType.INDEXING_COMPLETED: IndexingCompletedEvent,
        EventType.INDEXING_FAILED: IndexingFailedEvent,
        EventType.QUIZ_GENERATION_STARTED: QuizGenerationStartedEvent,
        EventType.QUIZ_GENERATION_PROGRESS: QuizGenerationProgressEvent,
        EventType.QUIZ_GENERATED: QuizGeneratedEvent,
        EventType.QUIZ_GENERATION_FAILED: QuizGenerationFailedEvent,
        EventType.TASK_STATUS_UPDATE: TaskStatusUpdateEvent,
        EventType.USER_NOTIFICATION: UserNotificationEvent,
        EventType.DLQ_MESSAGE: DLQMessageEvent,
        EventType.DLQ_PROCESSED: DLQProcessedEvent,
    }
    
    event_class = event_classes.get(event_type)
    if not event_class:
        raise ValueError(f"Unknown event type: {event_type}")
    
    # Set the event_type in kwargs to ensure it's properly set
    kwargs['event_type'] = event_type
    
    return event_class(**kwargs) 