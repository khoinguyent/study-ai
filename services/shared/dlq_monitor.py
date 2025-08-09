"""
Dead Letter Queue Monitor for Study AI Platform
Handles monitoring and processing of failed tasks in dead letter queues
"""

import json
import redis
import logging
from typing import Dict, Any, Optional, List
from celery import Celery
from .event_publisher import EventPublisher
from .events import EventType

logger = logging.getLogger(__name__)

class DLQMonitor:
    """Monitor and process dead letter queue messages"""
    
    def __init__(self, redis_url: str = "redis://localhost:6379", celery_app: Celery = None):
        self.redis_client = redis.from_url(redis_url)
        self.celery_app = celery_app
        self.event_publisher = EventPublisher(redis_url)
        
        # DLQ queue names
        self.dlq_queues = {
            'dlq_document': 'document_queue',
            'dlq_indexing': 'indexing_queue', 
            'dlq_quiz': 'quiz_queue'
        }
    
    def get_dlq_stats(self) -> Dict[str, Any]:
        """Get statistics about dead letter queues"""
        stats = {}
        
        for dlq_name, original_queue in self.dlq_queues.items():
            try:
                # Get queue length
                queue_length = self.redis_client.llen(dlq_name)
                
                # Get some sample messages (first 5)
                sample_messages = []
                if queue_length > 0:
                    messages = self.redis_client.lrange(dlq_name, 0, 4)
                    for msg in messages:
                        try:
                            sample_messages.append(json.loads(msg))
                        except json.JSONDecodeError:
                            sample_messages.append({"error": "Invalid JSON"})
                
                stats[dlq_name] = {
                    'queue_length': queue_length,
                    'original_queue': original_queue,
                    'sample_messages': sample_messages
                }
                
            except Exception as e:
                logger.error(f"Error getting stats for {dlq_name}: {str(e)}")
                stats[dlq_name] = {
                    'queue_length': 0,
                    'original_queue': original_queue,
                    'error': str(e)
                }
        
        return stats
    
    def list_dlq_messages(self, dlq_name: str, limit: int = 10) -> List[Dict[str, Any]]:
        """List messages in a specific DLQ"""
        try:
            messages = self.redis_client.lrange(dlq_name, 0, limit - 1)
            result = []
            
            for msg in messages:
                try:
                    parsed_msg = json.loads(msg)
                    result.append(parsed_msg)
                except json.JSONDecodeError:
                    result.append({
                        "error": "Invalid JSON",
                        "raw_message": msg.decode('utf-8', errors='ignore')
                    })
            
            return result
            
        except Exception as e:
            logger.error(f"Error listing messages from {dlq_name}: {str(e)}")
            return []
    
    def retry_dlq_message(self, dlq_name: str, message_index: int) -> bool:
        """Retry a specific message from DLQ"""
        try:
            # Get the message from DLQ
            message = self.redis_client.lindex(dlq_name, message_index)
            if not message:
                logger.error(f"Message at index {message_index} not found in {dlq_name}")
                return False
            
            # Parse the message
            task_data = json.loads(message)
            
            # Extract task information
            task_name = task_data.get('task', '')
            task_args = task_data.get('args', [])
            task_kwargs = task_data.get('kwargs', {})
            
            # Get original queue
            original_queue = self.dlq_queues.get(dlq_name)
            if not original_queue:
                logger.error(f"Unknown DLQ: {dlq_name}")
                return False
            
            # Retry the task
            if self.celery_app:
                task = self.celery_app.send_task(
                    task_name,
                    args=task_args,
                    kwargs=task_kwargs,
                    queue=original_queue
                )
                
                # Remove from DLQ
                self.redis_client.lrem(dlq_name, 1, message)
                
                # Publish DLQ processed event
                self.event_publisher.publish_dlq_processed(
                    task_id=task.id,
                    task_name=task_name,
                    processing_result="retried",
                    processing_notes=f"Retried from {dlq_name} to {original_queue}"
                )
                
                logger.info(f"Retried task {task_name} from {dlq_name} to {original_queue}")
                return True
            else:
                logger.error("Celery app not configured for retry")
                return False
                
        except Exception as e:
            logger.error(f"Error retrying message from {dlq_name}: {str(e)}")
            return False
    
    def discard_dlq_message(self, dlq_name: str, message_index: int) -> bool:
        """Discard a specific message from DLQ"""
        try:
            # Get the message from DLQ
            message = self.redis_client.lindex(dlq_name, message_index)
            if not message:
                logger.error(f"Message at index {message_index} not found in {dlq_name}")
                return False
            
            # Parse the message
            task_data = json.loads(message)
            task_name = task_data.get('task', '')
            
            # Remove from DLQ
            self.redis_client.lrem(dlq_name, 1, message)
            
            # Publish DLQ processed event
            self.event_publisher.publish_dlq_processed(
                task_id=task_data.get('id', 'unknown'),
                task_name=task_name,
                processing_result="discarded",
                processing_notes=f"Discarded from {dlq_name}"
            )
            
            logger.info(f"Discarded task {task_name} from {dlq_name}")
            return True
            
        except Exception as e:
            logger.error(f"Error discarding message from {dlq_name}: {str(e)}")
            return False
    
    def clear_dlq(self, dlq_name: str) -> bool:
        """Clear all messages from a DLQ"""
        try:
            # Get queue length before clearing
            queue_length = self.redis_client.llen(dlq_name)
            
            # Clear the queue
            self.redis_client.delete(dlq_name)
            
            # Publish DLQ processed event
            self.event_publisher.publish_dlq_processed(
                task_id="bulk_clear",
                task_name="dlq_clear",
                processing_result="cleared",
                processing_notes=f"Cleared {queue_length} messages from {dlq_name}"
            )
            
            logger.info(f"Cleared {queue_length} messages from {dlq_name}")
            return True
            
        except Exception as e:
            logger.error(f"Error clearing {dlq_name}: {str(e)}")
            return False
    
    def get_dlq_health(self) -> Dict[str, Any]:
        """Get health status of all DLQs"""
        health = {
            'status': 'healthy',
            'total_failed_tasks': 0,
            'queues': {}
        }
        
        total_failed = 0
        
        for dlq_name in self.dlq_queues.keys():
            try:
                queue_length = self.redis_client.llen(dlq_name)
                total_failed += queue_length
                
                health['queues'][dlq_name] = {
                    'status': 'healthy' if queue_length == 0 else 'warning',
                    'failed_tasks': queue_length,
                    'threshold_exceeded': queue_length > 10  # Warning threshold
                }
                
                if queue_length > 10:
                    health['status'] = 'warning'
                    
            except Exception as e:
                health['queues'][dlq_name] = {
                    'status': 'error',
                    'error': str(e)
                }
                health['status'] = 'error'
        
        health['total_failed_tasks'] = total_failed
        
        return health
