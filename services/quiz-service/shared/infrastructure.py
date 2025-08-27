"""
Infrastructure Abstraction Layer for Study AI Platform
Handles both local and cloud environments using Strategy and Factory patterns
"""

from abc import ABC, abstractmethod
from typing import Optional, Dict, Any
import os
import logging
from enum import Enum

logger = logging.getLogger(__name__)

class Environment(Enum):
    """Environment types"""
    LOCAL = "local"
    CLOUD = "cloud"

class InfrastructureProvider(Enum):
    """Infrastructure providers"""
    LOCAL = "local"
    AWS = "aws"
    # Future: GCP, Azure, etc.

class MessageBrokerType(Enum):
    """Message broker types"""
    REDIS = "redis"
    ELASTICACHE = "elasticache"
    # Future: RabbitMQ, SQS, etc.

class TaskQueueType(Enum):
    """Task queue types"""
    CELERY = "celery"
    SQS = "sqs"
    # Future: Temporal, etc.

class InfrastructureConfig:
    """Configuration for infrastructure components"""
    
    def __init__(self):
        self.environment = os.getenv('ENVIRONMENT', 'local').lower()
        self.provider = os.getenv('INFRASTRUCTURE_PROVIDER', 'local').lower()
        
        # Message broker configuration
        self.message_broker_type = os.getenv('MESSAGE_BROKER_TYPE', 'redis').lower()
        self.message_broker_url = os.getenv('MESSAGE_BROKER_URL')
        
        # Task queue configuration
        self.task_queue_type = os.getenv('TASK_QUEUE_TYPE', 'celery').lower()
        self.task_queue_url = os.getenv('TASK_QUEUE_URL')
        
        # AWS specific configuration
        self.aws_region = os.getenv('AWS_REGION', 'us-east-1')
        self.aws_access_key_id = os.getenv('AWS_ACCESS_KEY_ID')
        self.aws_secret_access_key = os.getenv('AWS_SECRET_ACCESS_KEY')
        
        # Redis/ElastiCache configuration
        self.redis_host = os.getenv('REDIS_HOST', 'redis')
        self.redis_port = int(os.getenv('REDIS_PORT', '6379'))
        self.redis_password = os.getenv('REDIS_PASSWORD')
        self.redis_db = int(os.getenv('REDIS_DB', '0'))
        
        # SQS configuration
        self.sqs_queue_url = os.getenv('SQS_QUEUE_URL')
        self.sqs_region = os.getenv('SQS_REGION', 'us-east-1')
        
        # Validate configuration
        self._validate_config()
    
    def _validate_config(self):
        """Validate the configuration"""
        if self.environment not in [e.value for e in Environment]:
            raise ValueError(f"Invalid environment: {self.environment}")
        
        if self.provider not in [p.value for p in InfrastructureProvider]:
            raise ValueError(f"Invalid infrastructure provider: {self.provider}")
        
        if self.message_broker_type not in [b.value for b in MessageBrokerType]:
            raise ValueError(f"Invalid message broker type: {self.message_broker_type}")
        
        if self.task_queue_type not in [q.value for q in TaskQueueType]:
            raise ValueError(f"Invalid task queue type: {self.task_queue_type}")
    
    @property
    def is_local(self) -> bool:
        """Check if running in local environment"""
        return self.environment == Environment.LOCAL.value
    
    @property
    def is_cloud(self) -> bool:
        """Check if running in cloud environment"""
        return self.environment == Environment.CLOUD.value
    
    @property
    def is_aws(self) -> bool:
        """Check if using AWS infrastructure"""
        return self.provider == InfrastructureProvider.AWS.value
    
    def get_message_broker_url(self) -> str:
        """Get the message broker URL based on configuration"""
        if self.message_broker_url:
            return self.message_broker_url
        
        if self.is_local:
            return f"redis://{self.redis_host}:{self.redis_port}/{self.redis_db}"
        elif self.is_aws and self.message_broker_type == MessageBrokerType.ELASTICACHE.value:
            # For ElastiCache, construct the URL
            if self.redis_password:
                return f"redis://:{self.redis_password}@{self.redis_host}:{self.redis_port}/{self.redis_db}"
            else:
                return f"redis://{self.redis_host}:{self.redis_port}/{self.redis_db}"
        
        # Fallback to local Redis
        return f"redis://{self.redis_host}:{self.redis_port}/{self.redis_db}"
    
    def get_task_queue_url(self) -> str:
        """Get the task queue URL based on configuration"""
        if self.task_queue_url:
            return self.task_queue_url
        
        if self.is_local:
            return self.get_message_broker_url()
        elif self.is_aws and self.task_queue_type == TaskQueueType.SQS.value:
            return self.sqs_queue_url or ""
        
        # Fallback to message broker URL
        return self.get_message_broker_url()

# Global infrastructure configuration instance
infra_config = InfrastructureConfig()

class MessageBroker(ABC):
    """Abstract base class for message brokers"""
    
    @abstractmethod
    def connect(self) -> bool:
        """Connect to the message broker"""
        pass
    
    @abstractmethod
    def disconnect(self):
        """Disconnect from the message broker"""
        pass
    
    @abstractmethod
    def publish(self, channel: str, message: str) -> bool:
        """Publish a message to a channel"""
        pass
    
    @abstractmethod
    def subscribe(self, channel: str, callback) -> bool:
        """Subscribe to a channel"""
        pass
    
    @abstractmethod
    def is_connected(self) -> bool:
        """Check if connected to the broker"""
        pass

class TaskQueue(ABC):
    """Abstract base class for task queues"""
    
    @abstractmethod
    def connect(self) -> bool:
        """Connect to the task queue"""
        pass
    
    @abstractmethod
    def disconnect(self):
        """Disconnect from the task queue"""
        pass
    
    @abstractmethod
    def enqueue(self, task_name: str, args: tuple = None, kwargs: dict = None) -> str:
        """Enqueue a task"""
        pass
    
    @abstractmethod
    def dequeue(self, timeout: int = 30) -> Optional[Dict[str, Any]]:
        """Dequeue a task"""
        pass
    
    @abstractmethod
    def is_connected(self) -> bool:
        """Check if connected to the queue"""
        pass

class RedisMessageBroker(MessageBroker):
    """Redis implementation of message broker"""
    
    def __init__(self, config: InfrastructureConfig):
        self.config = config
        self.client = None
        self.pubsub = None
    
    def connect(self) -> bool:
        """Connect to Redis"""
        try:
            import redis
            self.client = redis.from_url(self.config.get_message_broker_url())
            self.pubsub = self.client.pubsub()
            # Test connection
            self.client.ping()
            logger.info("Connected to Redis message broker")
            return True
        except Exception as e:
            logger.error(f"Failed to connect to Redis: {e}")
            return False
    
    def disconnect(self):
        """Disconnect from Redis"""
        if self.pubsub:
            self.pubsub.close()
        if self.client:
            self.client.close()
        logger.info("Disconnected from Redis message broker")
    
    def publish(self, channel: str, message: str) -> bool:
        """Publish message to Redis channel"""
        try:
            if self.client and self.is_connected():
                result = self.client.publish(channel, message)
                return result > 0
            return False
        except Exception as e:
            logger.error(f"Failed to publish message to Redis: {e}")
            return False
    
    def subscribe(self, channel: str, callback) -> bool:
        """Subscribe to Redis channel"""
        try:
            if self.pubsub and self.is_connected():
                self.pubsub.subscribe(channel)
                # Start listening in a separate thread
                import threading
                def listen():
                    for message in self.pubsub.listen():
                        if message['type'] == 'message':
                            callback(message['data'])
                
                thread = threading.Thread(target=listen, daemon=True)
                thread.start()
                return True
            return False
        except Exception as e:
            logger.error(f"Failed to subscribe to Redis channel: {e}")
            return False
    
    def is_connected(self) -> bool:
        """Check if connected to Redis"""
        try:
            return self.client and self.client.ping()
        except:
            return False

class ElastiCacheMessageBroker(MessageBroker):
    """ElastiCache implementation of message broker"""
    
    def __init__(self, config: InfrastructureConfig):
        self.config = config
        self.client = None
        self.pubsub = None
    
    def connect(self) -> bool:
        """Connect to ElastiCache"""
        try:
            import redis
            self.client = redis.from_url(self.config.get_message_broker_url())
            self.pubsub = self.client.pubsub()
            # Test connection
            self.client.ping()
            logger.info("Connected to ElastiCache message broker")
            return True
        except Exception as e:
            logger.error(f"Failed to connect to ElastiCache: {e}")
            return False
    
    def disconnect(self):
        """Disconnect from ElastiCache"""
        if self.pubsub:
            self.pubsub.close()
        if self.client:
            self.client.close()
        logger.info("Disconnected from ElastiCache message broker")
    
    def publish(self, channel: str, message: str) -> bool:
        """Publish message to ElastiCache channel"""
        try:
            if self.client and self.is_connected():
                result = self.client.publish(channel, message)
                return result > 0
            return False
        except Exception as e:
            logger.error(f"Failed to publish message to ElastiCache: {e}")
            return False
    
    def subscribe(self, channel: str, callback) -> bool:
        """Subscribe to ElastiCache channel"""
        try:
            if self.pubsub and self.is_connected():
                self.pubsub.subscribe(channel)
                # Start listening in a separate thread
                import threading
                def listen():
                    for message in self.pubsub.listen():
                        if message['type'] == 'message':
                            callback(message['data'])
                
                thread = threading.Thread(target=listen, daemon=True)
                thread.start()
                return True
            return False
        except Exception as e:
            logger.error(f"Failed to subscribe to ElastiCache channel: {e}")
            return False
    
    def is_connected(self) -> bool:
        """Check if connected to ElastiCache"""
        try:
            return self.client and self.client.ping()
        except:
            return False

class CeleryTaskQueue(TaskQueue):
    """Celery implementation of task queue"""
    
    def __init__(self, config: InfrastructureConfig):
        self.config = config
        self.app = None
    
    def connect(self) -> bool:
        """Connect to Celery"""
        try:
            from celery import Celery
            self.app = Celery(
                'study_ai',
                broker=self.config.get_task_queue_url(),
                backend=self.config.get_message_broker_url()
            )
            logger.info("Connected to Celery task queue")
            return True
        except Exception as e:
            logger.error(f"Failed to connect to Celery: {e}")
            return False
    
    def disconnect(self):
        """Disconnect from Celery"""
        if self.app:
            self.app.close()
        logger.info("Disconnected from Celery task queue")
    
    def enqueue(self, task_name: str, args: tuple = None, kwargs: dict = None) -> str:
        """Enqueue a Celery task"""
        try:
            if self.app and self.is_connected():
                task = self.app.send_task(task_name, args=args, kwargs=kwargs)
                return task.id
            return ""
        except Exception as e:
            logger.error(f"Failed to enqueue Celery task: {e}")
            return ""
    
    def dequeue(self, timeout: int = 30) -> Optional[Dict[str, Any]]:
        """Dequeue a Celery task (not applicable for Celery)"""
        logger.warning("Dequeue not applicable for Celery - use workers instead")
        return None
    
    def is_connected(self) -> bool:
        """Check if connected to Celery"""
        return self.app is not None

class SQSTaskQueue(TaskQueue):
    """AWS SQS implementation of task queue"""
    
    def __init__(self, config: InfrastructureConfig):
        self.config = config
        self.client = None
    
    def connect(self) -> bool:
        """Connect to SQS"""
        try:
            import boto3
            self.client = boto3.client(
                'sqs',
                region_name=self.config.aws_region,
                aws_access_key_id=self.config.aws_access_key_id,
                aws_secret_access_key=self.config.aws_secret_access_key
            )
            logger.info("Connected to SQS task queue")
            return True
        except Exception as e:
            logger.error(f"Failed to connect to SQS: {e}")
            return False
    
    def disconnect(self):
        """Disconnect from SQS"""
        self.client = None
        logger.info("Disconnected from SQS task queue")
    
    def enqueue(self, task_name: str, args: tuple = None, kwargs: dict = None) -> str:
        """Enqueue a task to SQS"""
        try:
            if self.client and self.is_connected():
                import json
                message_body = {
                    'task_name': task_name,
                    'args': args or [],
                    'kwargs': kwargs or {}
                }
                
                response = self.client.send_message(
                    QueueUrl=self.config.sqs_queue_url,
                    MessageBody=json.dumps(message_body)
                )
                return response['MessageId']
            return ""
        except Exception as e:
            logger.error(f"Failed to enqueue SQS task: {e}")
            return ""
    
    def dequeue(self, timeout: int = 30) -> Optional[Dict[str, Any]]:
        """Dequeue a task from SQS"""
        try:
            if self.client and self.is_connected():
                response = self.client.receive_message(
                    QueueUrl=self.config.sqs_queue_url,
                    MaxNumberOfMessages=1,
                    WaitTimeSeconds=min(timeout, 20)  # SQS max is 20 seconds
                )
                
                if 'Messages' in response:
                    message = response['Messages'][0]
                    import json
                    body = json.loads(message['Body'])
                    return {
                        'message_id': message['MessageId'],
                        'receipt_handle': message['ReceiptHandle'],
                        'task_name': body['task_name'],
                        'args': body['args'],
                        'kwargs': body['kwargs']
                    }
            return None
        except Exception as e:
            logger.error(f"Failed to dequeue SQS task: {e}")
            return None
    
    def is_connected(self) -> bool:
        """Check if connected to SQS"""
        return self.client is not None

class InfrastructureFactory:
    """Factory for creating infrastructure components"""
    
    @staticmethod
    def create_message_broker(config: InfrastructureConfig) -> MessageBroker:
        """Create a message broker based on configuration"""
        if config.message_broker_type == MessageBrokerType.REDIS.value:
            if config.is_local:
                return RedisMessageBroker(config)
            else:
                return ElastiCacheMessageBroker(config)
        elif config.message_broker_type == MessageBrokerType.ELASTICACHE.value:
            return ElastiCacheMessageBroker(config)
        else:
            raise ValueError(f"Unsupported message broker type: {config.message_broker_type}")
    
    @staticmethod
    def create_task_queue(config: InfrastructureConfig) -> TaskQueue:
        """Create a task queue based on configuration"""
        if config.task_queue_type == TaskQueueType.CELERY.value:
            return CeleryTaskQueue(config)
        elif config.task_queue_type == TaskQueueType.SQS.value:
            return SQSTaskQueue(config)
        else:
            raise ValueError(f"Unsupported task queue type: {config.task_queue_type}")

# Convenience functions for easy access
def get_message_broker() -> MessageBroker:
    """Get the configured message broker"""
    return InfrastructureFactory.create_message_broker(infra_config)

def get_task_queue() -> TaskQueue:
    """Get the configured task queue"""
    return InfrastructureFactory.create_task_queue(infra_config)

def is_local_environment() -> bool:
    """Check if running in local environment"""
    return infra_config.is_local

def is_cloud_environment() -> bool:
    """Check if running in cloud environment"""
    return infra_config.is_cloud

def get_redis_url() -> str:
    """Get Redis URL for backward compatibility"""
    return infra_config.get_message_broker_url()
