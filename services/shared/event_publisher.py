"""
Event Publisher Service for Study AI Platform
Handles publishing events to Redis pub/sub for event-driven communication
"""

import json
import redis
from typing import Dict, Any
from .events import BaseEvent, EventType, create_event
import logging

logger = logging.getLogger(__name__)

class EventPublisher:
    """Event publisher using Redis pub/sub"""
    
    def __init__(self, redis_url: str = "redis://localhost:6379"):
        self.redis_client = redis.from_url(redis_url)
        self.channel_prefix = "study_ai_events"
    
    def publish_event(self, event: BaseEvent) -> bool:
        """Publish an event to Redis pub/sub"""
        try:
            # Convert event to JSON
            event_data = event.model_dump()
            
            # Create channel name based on event type
            channel = f"{self.channel_prefix}:{event.event_type.value}"
            
            # Publish to Redis
            result = self.redis_client.publish(channel, json.dumps(event_data))
            
            logger.info(f"Published event {event.event_id} to channel {channel}")
            return result > 0
            
        except Exception as e:
            logger.error(f"Failed to publish event {event.event_id}: {str(e)}")
            return False
    
    def publish_document_uploaded(self, user_id: str, document_id: str, filename: str, 
                                file_size: int, content_type: str, service_name: str = "document-service") -> bool:
        """Publish document uploaded event"""
        event = create_event(
            EventType.DOCUMENT_UPLOADED,
            user_id=user_id,
            service_name=service_name,
            document_id=document_id,
            filename=filename,
            file_size=file_size,
            content_type=content_type
        )
        return self.publish_event(event)
    
    def publish_document_processing(self, user_id: str, document_id: str, 
                                  progress: int = 0, service_name: str = "document-service") -> bool:
        """Publish document processing event"""
        event = create_event(
            EventType.DOCUMENT_PROCESSING,
            user_id=user_id,
            service_name=service_name,
            document_id=document_id,
            progress=progress
        )
        return self.publish_event(event)
    
    def publish_document_processed(self, user_id: str, document_id: str, chunks_count: int,
                                 processing_time: float, service_name: str = "document-service") -> bool:
        """Publish document processed event"""
        event = create_event(
            EventType.DOCUMENT_PROCESSED,
            user_id=user_id,
            service_name=service_name,
            document_id=document_id,
            chunks_count=chunks_count,
            processing_time=processing_time
        )
        return self.publish_event(event)
    
    def publish_document_failed(self, user_id: str, document_id: str, error_message: str,
                              service_name: str = "document-service") -> bool:
        """Publish document failed event"""
        event = create_event(
            EventType.DOCUMENT_FAILED,
            user_id=user_id,
            service_name=service_name,
            document_id=document_id,
            error_message=error_message
        )
        return self.publish_event(event)
    
    def publish_indexing_started(self, user_id: str, document_id: str, chunks_count: int,
                               service_name: str = "indexing-service") -> bool:
        """Publish indexing started event"""
        event = create_event(
            EventType.INDEXING_STARTED,
            user_id=user_id,
            service_name=service_name,
            document_id=document_id,
            chunks_count=chunks_count
        )
        return self.publish_event(event)
    
    def publish_indexing_progress(self, user_id: str, document_id: str, progress: int,
                                processed_chunks: int, total_chunks: int,
                                service_name: str = "indexing-service") -> bool:
        """Publish indexing progress event"""
        event = create_event(
            EventType.INDEXING_PROGRESS,
            user_id=user_id,
            service_name=service_name,
            document_id=document_id,
            progress=progress,
            processed_chunks=processed_chunks,
            total_chunks=total_chunks
        )
        return self.publish_event(event)
    
    def publish_indexing_completed(self, user_id: str, document_id: str, vectors_count: int,
                                 indexing_time: float, service_name: str = "indexing-service") -> bool:
        """Publish indexing completed event"""
        event = create_event(
            EventType.INDEXING_COMPLETED,
            user_id=user_id,
            service_name=service_name,
            document_id=document_id,
            vectors_count=vectors_count,
            indexing_time=indexing_time
        )
        return self.publish_event(event)
    
    def publish_indexing_failed(self, user_id: str, document_id: str, error_message: str,
                              service_name: str = "indexing-service") -> bool:
        """Publish indexing failed event"""
        event = create_event(
            EventType.INDEXING_FAILED,
            user_id=user_id,
            service_name=service_name,
            document_id=document_id,
            error_message=error_message
        )
        return self.publish_event(event)
    
    def publish_quiz_generation_started(self, user_id: str, quiz_id: str, topic: str,
                                      difficulty: str, num_questions: int,
                                      service_name: str = "quiz-service") -> bool:
        """Publish quiz generation started event"""
        event = create_event(
            EventType.QUIZ_GENERATION_STARTED,
            user_id=user_id,
            service_name=service_name,
            quiz_id=quiz_id,
            topic=topic,
            difficulty=difficulty,
            num_questions=num_questions
        )
        return self.publish_event(event)
    
    def publish_quiz_generation_progress(self, user_id: str, quiz_id: str, progress: int,
                                       questions_generated: int, total_questions: int,
                                       service_name: str = "quiz-service") -> bool:
        """Publish quiz generation progress event"""
        event = create_event(
            EventType.QUIZ_GENERATION_PROGRESS,
            user_id=user_id,
            service_name=service_name,
            quiz_id=quiz_id,
            progress=progress,
            questions_generated=questions_generated,
            total_questions=total_questions
        )
        return self.publish_event(event)
    
    def publish_quiz_generated(self, user_id: str, quiz_id: str, questions_count: int,
                             generation_time: float, service_name: str = "quiz-service") -> bool:
        """Publish quiz generated event"""
        event = create_event(
            EventType.QUIZ_GENERATED,
            user_id=user_id,
            service_name=service_name,
            quiz_id=quiz_id,
            questions_count=questions_count,
            generation_time=generation_time
        )
        return self.publish_event(event)
    
    def publish_quiz_generation_failed(self, user_id: str, quiz_id: str, error_message: str,
                                     service_name: str = "quiz-service") -> bool:
        """Publish quiz generation failed event"""
        event = create_event(
            EventType.QUIZ_GENERATION_FAILED,
            user_id=user_id,
            service_name=service_name,
            quiz_id=quiz_id,
            error_message=error_message
        )
        return self.publish_event(event)
    
    def publish_task_status_update(self, user_id: str, task_id: str, task_type: str,
                                 status: str, progress: int = 0, message: str = None,
                                 service_name: str = "system") -> bool:
        """Publish task status update event"""
        event = create_event(
            EventType.TASK_STATUS_UPDATE,
            user_id=user_id,
            service_name=service_name,
            task_id=task_id,
            task_type=task_type,
            status=status,
            progress=progress,
            message=message
        )
        return self.publish_event(event)
    
    def publish_user_notification(self, user_id: str, notification_type: str, title: str,
                                message: str, priority: str = "normal",
                                service_name: str = "notification-service") -> bool:
        """Publish user notification event"""
        event = create_event(
            EventType.USER_NOTIFICATION,
            user_id=user_id,
            service_name=service_name,
            notification_type=notification_type,
            title=title,
            message=message,
            priority=priority
        )
        return self.publish_event(event) 