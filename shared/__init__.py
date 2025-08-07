"""
Shared module for Study AI Platform
Contains common utilities and classes used across services
"""

import redis
import json
from typing import Dict, Any, Optional
from enum import Enum

class EventType(str, Enum):
    """Event types for the event-driven architecture"""
    DOCUMENT_PROCESSING = "document_processing"
    DOCUMENT_PROCESSED = "document_processed"
    DOCUMENT_FAILED = "document_failed"
    INDEXING_STARTED = "indexing_started"
    INDEXING_COMPLETED = "indexing_completed"
    INDEXING_FAILED = "indexing_failed"
    QUIZ_GENERATION_STARTED = "quiz_generation_started"
    QUIZ_GENERATION_COMPLETED = "quiz_generation_completed"
    QUIZ_GENERATION_FAILED = "quiz_generation_failed"
    USER_NOTIFICATION = "user_notification"

class EventPublisher:
    """Publishes events to Redis for inter-service communication"""
    
    def __init__(self, redis_url: str):
        self.redis_client = redis.from_url(redis_url)
    
    def publish_event(self, event_type: EventType, data: Dict[str, Any]):
        """Publish an event to Redis"""
        event = {
            "type": event_type.value,
            "data": data,
            "timestamp": str(datetime.utcnow())
        }
        self.redis_client.publish("study_ai_events", json.dumps(event))
    
    def publish_document_processing(self, user_id: str, document_id: str, progress: int):
        """Publish document processing event"""
        self.publish_event(EventType.DOCUMENT_PROCESSING, {
            "user_id": user_id,
            "document_id": document_id,
            "progress": progress
        })
    
    def publish_document_processed(self, user_id: str, document_id: str, chunks_count: int, processing_time: float):
        """Publish document processed event"""
        self.publish_event(EventType.DOCUMENT_PROCESSED, {
            "user_id": user_id,
            "document_id": document_id,
            "chunks_count": chunks_count,
            "processing_time": processing_time
        })
    
    def publish_document_failed(self, user_id: str, document_id: str, error_message: str):
        """Publish document failed event"""
        self.publish_event(EventType.DOCUMENT_FAILED, {
            "user_id": user_id,
            "document_id": document_id,
            "error_message": error_message
        })
    
    def publish_user_notification(self, user_id: str, notification_type: str, title: str, message: str, priority: str = "normal"):
        """Publish user notification event"""
        self.publish_event(EventType.USER_NOTIFICATION, {
            "user_id": user_id,
            "notification_type": notification_type,
            "title": title,
            "message": message,
            "priority": priority
        })

# Import datetime for timestamp
from datetime import datetime 