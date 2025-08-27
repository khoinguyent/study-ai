"""
Event Publisher Service for Study AI Platform
Handles publishing events to message brokers using infrastructure abstraction
"""

import json
import logging
from typing import Optional, Dict, Any
from .events import BaseEvent, EventType, create_event
from .infrastructure import get_message_broker, is_local_environment

logger = logging.getLogger(__name__)

class EventPublisher:
    """Event publisher using infrastructure abstraction"""
    
    def __init__(self, message_broker=None):
        """
        Initialize event publisher
        
        Args:
            message_broker: Optional message broker instance. If None, will use infrastructure abstraction.
        """
        self.message_broker = message_broker
        self.channel_prefix = "study_ai_events"
        self._connected = False
    
    def _get_message_broker(self):
        """Get message broker instance"""
        if self.message_broker:
            return self.message_broker
        
        # Use infrastructure abstraction
        broker = get_message_broker()
        if not self._connected:
            self._connected = broker.connect()
        return broker
    
    def _publish_event(self, event: BaseEvent) -> bool:
        """Publish an event to the message broker"""
        try:
            broker = self._get_message_broker()
            if broker and broker.is_connected():
                channel = f"{self.channel_prefix}:{event.event_type.value}"
                message = json.dumps(event.model_dump())
                success = broker.publish(channel, message)
                if success:
                    logger.debug(f"Published event {event.event_type.value} to channel {channel}")
                return success
            else:
                logger.error("Message broker not connected")
                return False
        except Exception as e:
            logger.error(f"Failed to publish event: {e}")
            return False
    
    def publish_document_uploaded(self, user_id: str, document_id: str, filename: str, 
                                 file_size: int, content_type: str) -> bool:
        """Publish document uploaded event"""
        event = create_event(
            event_type=EventType.DOCUMENT_UPLOADED,
            user_id=user_id,
            document_id=document_id,
            service_name="document-service",
            filename=filename,
            file_size=file_size,
            content_type=content_type
        )
        return self._publish_event(event)
    
    def publish_document_processing(self, user_id: str, document_id: str, 
                                   progress: int = 0, message: str = "Processing started") -> bool:
        """Publish document processing event"""
        event = create_event(
            event_type=EventType.DOCUMENT_PROCESSING,
            user_id=user_id,
            document_id=document_id,
            service_name="document-service",
            metadata={
                "progress": progress,
                "message": message
            }
        )
        return self._publish_event(event)
    
    def publish_document_processed(self, user_id: str, document_id: str, 
                                  processing_time: float, chunks_count: int) -> bool:
        """Publish document processed event"""
        event = create_event(
            event_type=EventType.DOCUMENT_PROCESSED,
            user_id=user_id,
            document_id=document_id,
            service_name="document-service",
            metadata={
                "processing_time": processing_time,
                "chunks_count": chunks_count
            }
        )
        return self._publish_event(event)
    
    def publish_document_failed(self, user_id: str, document_id: str, 
                               error_message: str) -> bool:
        """Publish document failed event"""
        event = create_event(
            event_type=EventType.DOCUMENT_FAILED,
            user_id=user_id,
            document_id=document_id,
            service_name="document-service",
            metadata={
                "error": error_message
            }
        )
        return self._publish_event(event)
    
    def publish_indexing_started(self, user_id: str, document_id: str, 
                                chunks_count: int) -> bool:
        """Publish indexing started event"""
        event = create_event(
            event_type=EventType.INDEXING_STARTED,
            user_id=user_id,
            document_id=document_id,
            service_name="indexing-service",
            metadata={
                "chunks_count": chunks_count
            }
        )
        return self._publish_event(event)
    
    def publish_indexing_progress(self, user_id: str, document_id: str, 
                                 progress: int, message: str) -> bool:
        """Publish indexing progress event"""
        event = create_event(
            event_type=EventType.INDEXING_PROGRESS,
            user_id=user_id,
            document_id=document_id,
            service_name="indexing-service",
            metadata={
                "progress": progress,
                "message": message
            }
        )
        return self._publish_event(event)
    
    def publish_indexing_completed(self, user_id: str, document_id: str, 
                                  indexing_time: float, vectors_count: int) -> bool:
        """Publish indexing completed event"""
        event = create_event(
            event_type=EventType.INDEXING_COMPLETED,
            user_id=user_id,
            document_id=document_id,
            service_name="indexing-service",
            metadata={
                "indexing_time": indexing_time,
                "vectors_count": vectors_count
            }
        )
        return self._publish_event(event)
    
    def publish_indexing_failed(self, user_id: str, document_id: str, 
                               error_message: str) -> bool:
        """Publish indexing failed event"""
        event = create_event(
            event_type=EventType.INDEXING_FAILED,
            user_id=user_id,
            document_id=document_id,
            service_name="indexing-service",
            metadata={
                "error": error_message
            }
        )
        return self._publish_event(event)
    
    def publish_quiz_generation_started(self, user_id: str, quiz_id: str, 
                                       source_document_id: str, num_questions: int, 
                                       topic: str = "General", difficulty: str = "medium") -> bool:
        """Publish quiz generation started event"""
        event = create_event(
            event_type=EventType.QUIZ_GENERATION_STARTED,
            user_id=user_id,
            service_name="quiz-service",
            quiz_id=quiz_id,
            topic=topic,
            difficulty=difficulty,
            num_questions=num_questions
        )
        return self._publish_event(event)
    
    def publish_quiz_generation_progress(self, user_id: str, quiz_id: str, 
                                        progress: int, message: str) -> bool:
        """Publish quiz generation progress event"""
        event = create_event(
            event_type=EventType.QUIZ_GENERATION_PROGRESS,
            user_id=user_id,
            document_id=quiz_id,  # Use quiz_id as document_id for consistency
            service_name="quiz-service",
            metadata={
                "quiz_id": quiz_id,
                "progress": progress,
                "message": message
            }
        )
        return self._publish_event(event)
    
    def publish_quiz_generated(self, user_id: str, quiz_id: str, 
                               generation_time: float, questions_count: int) -> bool:
        """Publish quiz generated event"""
        event = create_event(
            event_type=EventType.QUIZ_GENERATED,
            user_id=user_id,
            document_id=quiz_id,  # Use quiz_id as document_id for consistency
            metadata={
                "quiz_id": quiz_id,
                "generation_time": generation_time,
                "questions_count": questions_count
            }
        )
        return self._publish_event(event)
    
    def publish_quiz_generation_failed(self, user_id: str, quiz_id: str, 
                                      error_message: str) -> bool:
        """Publish quiz generation failed event"""
        event = create_event(
            event_type=EventType.QUIZ_GENERATION_FAILED,
            user_id=user_id,
            document_id=quiz_id,  # Use quiz_id as document_id for consistency
            metadata={
                "quiz_id": quiz_id,
                "error": error_message
            }
        )
        return self._publish_event(event)
    
    def publish_task_status_update(self, user_id: str, task_id: str, task_type: str,
                                 status: str, progress: int, message: str, service_name: str = "document-service") -> bool:
        """Publish task status update event"""
        event = create_event(
            event_type=EventType.TASK_STATUS_UPDATE,
            user_id=user_id,
            service_name=service_name,
            task_id=task_id,
            task_type=task_type,
            status=status,
            progress=progress,
            message=message
        )
        return self._publish_event(event)
    
    def publish_user_notification(self, user_id: str, notification_type: str, 
                                 title: str, message: str, priority: str = "normal",
                                 metadata: Optional[Dict[str, Any]] = None) -> bool:
        """Publish user notification event"""
        event = create_event(
            event_type=EventType.USER_NOTIFICATION,
            user_id=user_id,
            service_name="notification-service",
            notification_type=notification_type,
            title=title,
            message=message,
            priority=priority,
            metadata=metadata or {}
        )
        return self._publish_event(event)
    
    def publish_dlq_event(self, task_id: str, task_name: str, error_message: str,
                          original_queue: str, retry_count: int = 0) -> bool:
        """Publish dead letter queue event"""
        event = create_event(
            event_type=EventType.DLQ_MESSAGE,  # Use DLQ_MESSAGE instead of DLQ_ALERT
            user_id="system",
            document_id=task_id,  # Use task_id as document_id for consistency
            service_name="system",
            metadata={
                "task_id": task_id,
                "task_name": task_name,
                "error": error_message,
                "queue": original_queue,
                "retry_count": retry_count
            }
        )
        return self._publish_event(event)
    
    def disconnect(self):
        """Disconnect from message broker"""
        if self.message_broker and self._connected:
            self.message_broker.disconnect()
            self._connected = False
        elif self._connected:
            # Get broker from infrastructure and disconnect
            broker = get_message_broker()
            broker.disconnect()
            self._connected = False

# Backward compatibility: create default instance
default_event_publisher = EventPublisher()

# Convenience functions for backward compatibility
def publish_document_uploaded(user_id: str, document_id: str, filename: str, 
                             file_size: int, content_type: str) -> bool:
    """Publish document uploaded event (backward compatibility)"""
    return default_event_publisher.publish_document_uploaded(
        user_id, document_id, filename, file_size, content_type
    )

def publish_document_processing(user_id: str, document_id: str, 
                               progress: int = 0, message: str = "Processing started") -> bool:
    """Publish document processing event (backward compatibility)"""
    return default_event_publisher.publish_document_processing(
        user_id, document_id, progress, message
    )

def publish_document_processed(user_id: str, document_id: str, 
                              processing_time: float, chunks_count: int) -> bool:
    """Publish document processed event (backward compatibility)"""
    return default_event_publisher.publish_document_processed(
        user_id, document_id, processing_time, chunks_count
    )

def publish_document_failed(user_id: str, document_id: str, error_message: str) -> bool:
    """Publish document failed event (backward compatibility)"""
    return default_event_publisher.publish_document_failed(
        user_id, document_id, error_message
    )

def publish_task_status_update(user_id: str, task_id: str, task_type: str,
                             status: str, progress: int, message: str) -> bool:
    """Publish task status update event (backward compatibility)"""
    return default_event_publisher.publish_task_status_update(
        user_id, task_id, task_type, status, progress, message
    ) 