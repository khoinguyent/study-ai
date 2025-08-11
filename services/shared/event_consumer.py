"""
Event Consumer Service for Study AI Platform
Handles consuming events from message brokers using infrastructure abstraction
"""

import json
import threading
import time
from typing import Callable, Dict, List, Any
from .events import BaseEvent, EventType, create_event
from .infrastructure import get_message_broker, is_local_environment
import logging
import asyncio

logger = logging.getLogger(__name__)

class EventConsumer:
    """Event consumer using infrastructure abstraction"""
    
    def __init__(self, message_broker=None):
        """
        Initialize event consumer
        
        Args:
            message_broker: Optional message broker instance. If None, will use infrastructure abstraction.
        """
        self.message_broker = message_broker
        self.channel_prefix = "study_ai_events"
        self.handlers: Dict[str, List[Callable]] = {}
        self.running = False
        self.thread = None
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
    
    def subscribe_to_event(self, event_type: EventType, handler: Callable[[BaseEvent], None]):
        """Subscribe to a specific event type"""
        channel = f"{self.channel_prefix}:{event_type.value}"
        
        if channel not in self.handlers:
            self.handlers[channel] = []
            # Subscribe to message broker channel
            broker = self._get_message_broker()
            if broker and broker.is_connected():
                broker.subscribe(channel, self._handle_message)
                logger.info(f"Subscribed to channel: {channel}")
        
        self.handlers[channel].append(handler)
        logger.info(f"Added handler for event type: {event_type.value}")
    
    def subscribe_to_all_events(self, handler: Callable[[BaseEvent], None]):
        """Subscribe to all event types"""
        for event_type in EventType:
            self.subscribe_to_event(event_type, handler)
    
    def subscribe_to_document_events(self, handler: Callable[[BaseEvent], None]):
        """Subscribe to all document-related events"""
        document_events = [
            EventType.DOCUMENT_UPLOADED,
            EventType.DOCUMENT_PROCESSING,
            EventType.DOCUMENT_PROCESSED,
            EventType.DOCUMENT_FAILED
        ]
        for event_type in document_events:
            self.subscribe_to_event(event_type, handler)
    
    def subscribe_to_indexing_events(self, handler: Callable[[BaseEvent], None]):
        """Subscribe to all indexing-related events"""
        indexing_events = [
            EventType.INDEXING_STARTED,
            EventType.INDEXING_PROGRESS,
            EventType.INDEXING_COMPLETED,
            EventType.INDEXING_FAILED
        ]
        for event_type in indexing_events:
            self.subscribe_to_event(event_type, handler)
    
    def subscribe_to_quiz_events(self, handler: Callable[[BaseEvent], None]):
        """Subscribe to all quiz-related events"""
        quiz_events = [
            EventType.QUIZ_GENERATION_STARTED,
            EventType.QUIZ_GENERATION_PROGRESS,
            EventType.QUIZ_GENERATED,
            EventType.QUIZ_GENERATION_FAILED
        ]
        for event_type in quiz_events:
            self.subscribe_to_event(event_type, handler)
    
    def subscribe_to_task_events(self, handler: Callable[[BaseEvent], None]):
        """Subscribe to all task-related events"""
        task_events = [
            EventType.TASK_STATUS_UPDATE,
            EventType.USER_NOTIFICATION,
            EventType.DLQ_ALERT
        ]
        for event_type in task_events:
            self.subscribe_to_event(event_type, handler)
    
    def _handle_message(self, message_data):
        """Handle incoming message from message broker"""
        try:
            # Parse message data
            if isinstance(message_data, bytes):
                message_data = message_data.decode('utf-8')
            
            # Parse JSON message
            event_data = json.loads(message_data)
            
            # Create event object
            event = BaseEvent(**event_data)
            
            # Find channel for this event type
            channel = f"{self.channel_prefix}:{event.event_type.value}"
            
            # Call all handlers for this channel
            if channel in self.handlers:
                for handler in self.handlers[channel]:
                    try:
                        handler(event)
                    except Exception as e:
                        logger.error(f"Error in event handler for {event.event_type.value}: {e}")
            else:
                logger.warning(f"No handlers found for channel: {channel}")
                
        except Exception as e:
            logger.error(f"Error handling message: {e}")
    
    def start(self):
        """Start consuming events"""
        if self.running:
            logger.warning("Event consumer is already running")
            return
        
        try:
            broker = self._get_message_broker()
            if broker and broker.is_connected():
                self.running = True
                logger.info("Event consumer started successfully")
            else:
                logger.error("Failed to start event consumer: message broker not connected")
        except Exception as e:
            logger.error(f"Failed to start event consumer: {e}")
    
    def stop(self):
        """Stop consuming events"""
        if not self.running:
            logger.warning("Event consumer is not running")
            return
        
        self.running = False
        logger.info("Event consumer stopped")
    
    def is_running(self) -> bool:
        """Check if event consumer is running"""
        return self.running
    
    def get_subscribed_channels(self) -> List[str]:
        """Get list of subscribed channels"""
        return list(self.handlers.keys())
    
    def get_handler_count(self, event_type: EventType) -> int:
        """Get number of handlers for a specific event type"""
        channel = f"{self.channel_prefix}:{event_type.value}"
        return len(self.handlers.get(channel, []))
    
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
default_event_consumer = EventConsumer()

# Convenience functions for backward compatibility
def subscribe_to_event(event_type: EventType, handler: Callable[[BaseEvent], None]):
    """Subscribe to a specific event type (backward compatibility)"""
    return default_event_consumer.subscribe_to_event(event_type, handler)

def subscribe_to_all_events(handler: Callable[[BaseEvent], None]):
    """Subscribe to all event types (backward compatibility)"""
    return default_event_consumer.subscribe_to_all_events(handler)

def subscribe_to_document_events(handler: Callable[[BaseEvent], None]):
    """Subscribe to all document-related events (backward compatibility)"""
    return default_event_consumer.subscribe_to_document_events(handler)

def start_event_consumer():
    """Start the event consumer (backward compatibility)"""
    return default_event_consumer.start()

def stop_event_consumer():
    """Stop the event consumer (backward compatibility)"""
    return default_event_consumer.stop() 