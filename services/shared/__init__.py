"""
Shared Module for Study AI Platform
Contains common utilities, events, and services used across all microservices
"""

from .events import (
    EventType, TaskStatus, BaseEvent, create_event,
    DocumentUploadedEvent, DocumentProcessingEvent, DocumentProcessedEvent, DocumentFailedEvent,
    IndexingStartedEvent, IndexingProgressEvent, IndexingCompletedEvent, IndexingFailedEvent,
    QuizGenerationStartedEvent, QuizGenerationProgressEvent, QuizGeneratedEvent, QuizGenerationFailedEvent,
    TaskStatusUpdateEvent, UserNotificationEvent
)

from .event_publisher import EventPublisher
from .event_consumer import EventConsumer
# AsyncEventConsumer temporarily removed - import issues being resolved

__all__ = [
    # Events
    'EventType', 'TaskStatus', 'BaseEvent', 'create_event',
    'DocumentUploadedEvent', 'DocumentProcessingEvent', 'DocumentProcessedEvent', 'DocumentFailedEvent',
    'IndexingStartedEvent', 'IndexingProgressEvent', 'IndexingCompletedEvent', 'IndexingFailedEvent',
    'QuizGenerationStartedEvent', 'QuizGenerationProgressEvent', 'QuizGeneratedEvent', 'QuizGenerationFailedEvent',
    'TaskStatusUpdateEvent', 'UserNotificationEvent',
    
    # Event Services
    'EventPublisher', 'EventConsumer'
    # 'AsyncEventConsumer' temporarily removed - import issues being resolved
] 