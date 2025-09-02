"""
Event Consumer Service for Study AI Platform
Handles consuming events from Redis pub/sub for event-driven communication
"""

import json
import redis
import threading
import time
from typing import Callable, Dict, List, Any
from .events import BaseEvent, EventType, create_event
import logging
import asyncio

logger = logging.getLogger(__name__)

class EventConsumer:
    """Event consumer using Redis pub/sub"""
    
    def __init__(self, redis_url: str = "redis://localhost:6379"):
        self.redis_client = redis.from_url(redis_url)
        self.pubsub = self.redis_client.pubsub()
        self.channel_prefix = "study_ai_events"
        self.handlers: Dict[str, List[Callable]] = {}
        self.running = False
        self.thread = None
    
    def subscribe_to_event(self, event_type: EventType, handler: Callable[[BaseEvent], None]):
        """Subscribe to a specific event type"""
        channel = f"{self.channel_prefix}:{event_type.value}"
        
        if channel not in self.handlers:
            self.handlers[channel] = []
            # Subscribe to Redis channel
            self.pubsub.subscribe(channel)
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
    
    def _parse_event(self, message_data: str) -> BaseEvent:
        """Parse event from JSON message"""
        try:
            data = json.loads(message_data)
            event_type = EventType(data.get('event_type'))
            # Remove event_type from data to avoid duplicate argument error
            event_data = {k: v for k, v in data.items() if k != 'event_type'}
            return create_event(event_type, **event_data)
        except Exception as e:
            logger.error(f"Failed to parse event: {str(e)}")
            raise
    
    def _handle_message(self, message):
        """Handle incoming Redis message"""
        if message['type'] != 'message':
            return
        
        try:
            channel = message['channel'].decode('utf-8')
            data = message['data'].decode('utf-8')
            
            # Parse event
            event = self._parse_event(data)
            
            # Call handlers
            if channel in self.handlers:
                for handler in self.handlers[channel]:
                    try:
                        handler(event)
                    except Exception as e:
                        logger.error(f"Handler error for event {event.event_id}: {str(e)}")
            
            logger.debug(f"Processed event {event.event_id} from channel {channel}")
            
        except Exception as e:
            logger.error(f"Failed to handle message: {str(e)}")
    
    def start(self):
        """Start consuming events"""
        if self.running:
            logger.warning("Event consumer is already running")
            return
        
        self.running = True
        self.thread = threading.Thread(target=self._consume_events, daemon=True)
        self.thread.start()
        logger.info("Event consumer started")
    
    def stop(self):
        """Stop consuming events"""
        self.running = False
        if self.pubsub:
            self.pubsub.close()
        if self.thread:
            self.thread.join(timeout=5)
        logger.info("Event consumer stopped")
    
    def _consume_events(self):
        """Main event consumption loop"""
        while self.running:
            try:
                # Get message with timeout
                message = self.pubsub.get_message(timeout=1.0)
                if message:
                    self._handle_message(message)
            except Exception as e:
                logger.error(f"Error in event consumption loop: {str(e)}")
                time.sleep(1)  # Wait before retrying

class AsyncEventConsumer:
    """Async event consumer for use with async/await"""
    
    def __init__(self, redis_url: str = "redis://localhost:6379"):
        self.redis_client = redis.from_url(redis_url)
        self.channel_prefix = "study_ai_events"
        self.handlers: Dict[str, List[Callable]] = {}
    
    async def subscribe_to_event(self, event_type: EventType, handler: Callable[[BaseEvent], None]):
        """Subscribe to a specific event type"""
        channel = f"{self.channel_prefix}:{event_type.value}"
        
        if channel not in self.handlers:
            self.handlers[channel] = []
        
        self.handlers[channel].append(handler)
        logger.info(f"Added async handler for event type: {event_type.value}")
    
    async def listen_for_events(self):
        """Listen for events asynchronously"""
        pubsub = self.redis_client.pubsub()
        
        # Subscribe to all channels
        for channel in self.handlers.keys():
            pubsub.subscribe(channel)
        
        try:
            for message in pubsub.listen():
                if message['type'] == 'message':
                    await self._handle_message_async(message)
        except Exception as e:
            logger.error(f"Error in async event listener: {str(e)}")
        finally:
            pubsub.close()
    
    async def _handle_message_async(self, message):
        """Handle incoming Redis message asynchronously"""
        try:
            channel = message['channel'].decode('utf-8')
            data = message['data'].decode('utf-8')
            
            # Parse event
            event = self._parse_event(data)
            
            # Call handlers
            if channel in self.handlers:
                for handler in self.handlers[channel]:
                    try:
                        if asyncio.iscoroutinefunction(handler):
                            await handler(event)
                        else:
                            handler(event)
                    except Exception as e:
                        logger.error(f"Async handler error for event {event.event_id}: {str(e)}")
            
            logger.debug(f"Processed async event {event.event_id} from channel {channel}")
            
        except Exception as e:
            logger.error(f"Failed to handle async message: {str(e)}")
    
    def _parse_event(self, message_data: str) -> BaseEvent:
        """Parse event from JSON message"""
        try:
            data = json.loads(message_data)
            event_type = EventType(data.get('event_type'))
            # Remove event_type from data to avoid duplicate argument error
            event_data = {k: v for k, v in data.items() if k != 'event_type'}
            return create_event(event_type, **event_data)
        except Exception as e:
            logger.error(f"Failed to parse event: {str(e)}")
            raise 