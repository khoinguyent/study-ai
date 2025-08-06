# Event-Driven Architecture for Study AI Platform

## Overview

The Study AI Platform uses an event-driven architecture with Redis pub/sub and Celery for handling long-running tasks like document processing, indexing, and quiz generation. This architecture ensures real-time notifications and scalable task processing.

## Architecture Components

### 1. Event System
- **Redis Pub/Sub**: Message broker for event communication
- **Event Publisher**: Publishes events to Redis channels
- **Event Consumer**: Subscribes to events and processes them
- **Event Types**: Defined event schemas for different operations

### 2. Task Processing
- **Celery**: Background task processing with Redis as broker
- **Task Queues**: Separate queues for different service types
- **Event-Driven Tasks**: Tasks that publish events for status updates

### 3. Real-time Notifications
- **WebSocket Manager**: Handles real-time connections
- **Notification Service**: Consumes events and sends notifications
- **User Notifications**: In-app notifications for task status

## Event Flow

```
User Upload → Document Service → Event Publisher → Redis Pub/Sub → Event Consumer → Notification Service → WebSocket → User
```

### Detailed Flow:

1. **Document Upload**
   ```
   User uploads document → Document Service → publish_document_uploaded() → Redis
   ```

2. **Document Processing**
   ```
   Document Service → process_document() → publish_document_processing() → Redis
   ```

3. **Indexing Trigger**
   ```
   Document Service → trigger_indexing() → Indexing Service → publish_indexing_started() → Redis
   ```

4. **Quiz Generation**
   ```
   Quiz Service → generate_quiz() → publish_quiz_generation_started() → Redis
   ```

5. **Notification Delivery**
   ```
   Notification Service → consume events → create notifications → WebSocket → User
   ```

## Event Types

### Document Events
- `document.uploaded`: Document uploaded successfully
- `document.processing`: Document processing started
- `document.processed`: Document processing completed
- `document.failed`: Document processing failed

### Indexing Events
- `indexing.started`: Indexing process started
- `indexing.progress`: Indexing progress update
- `indexing.completed`: Indexing completed
- `indexing.failed`: Indexing failed

### Quiz Events
- `quiz.generation.started`: Quiz generation started
- `quiz.generation.progress`: Quiz generation progress
- `quiz.generated`: Quiz generated successfully
- `quiz.generation.failed`: Quiz generation failed

### System Events
- `task.status.update`: General task status update
- `user.notification`: User notification event

## Implementation

### 1. Event Publisher Usage

```python
from services.shared import EventPublisher

# Initialize publisher
publisher = EventPublisher(redis_url="redis://localhost:6379")

# Publish document uploaded event
publisher.publish_document_uploaded(
    user_id="user123",
    document_id="doc456",
    filename="document.pdf",
    file_size=1024000,
    content_type="application/pdf"
)

# Publish task status update
publisher.publish_task_status_update(
    user_id="user123",
    task_id="task789",
    task_type="document_processing",
    status="processing",
    progress=50,
    message="Processing document..."
)
```

### 2. Event Consumer Usage

```python
from services.shared import EventConsumer, EventType

# Initialize consumer
consumer = EventConsumer(redis_url="redis://localhost:6379")

# Subscribe to specific events
def handle_document_event(event):
    print(f"Document event: {event.event_type} for document {event.document_id}")

consumer.subscribe_to_document_events(handle_document_event)

# Start consuming events
consumer.start()
```

### 3. Celery Task with Events

```python
from services.shared.celery_app import document_task, EventDrivenTask

@document_task
def process_document_task(self, document_id: str, user_id: str):
    task_handler = EventDrivenTask()
    task_id = f"doc_process_{document_id}"
    
    try:
        # Publish task started
        task_handler.publish_task_started(task_id, user_id, "document_processing")
        
        # Process document
        # ... processing logic ...
        
        # Publish progress updates
        task_handler.publish_task_progress(task_id, user_id, "document_processing", 50, "Processing...")
        
        # Publish completion
        task_handler.publish_task_completed(task_id, user_id, "document_processing", "Document processed!")
        
    except Exception as e:
        task_handler.publish_task_failed(task_id, user_id, "document_processing", str(e))
        raise
```

### 4. Notification Service Integration

```python
# In notification service
async def handle_document_event(event):
    # Create notification in database
    notification = Notification(
        user_id=event.user_id,
        title=f"Document {event.event_type.value}",
        message=f"Document {event.document_id} status updated",
        notification_type="document_status"
    )
    db.add(notification)
    db.commit()
    
    # Send WebSocket notification
    await websocket_manager.send_personal_message(
        user_id=event.user_id,
        message={
            "type": "document_status",
            "event": event.event_type.value,
            "document_id": event.document_id
        }
    )
```

## Configuration

### Redis Configuration
```yaml
# docker-compose.dev.yml
redis:
  image: redis:7-alpine
  ports:
    - "6379:6379"
  command: redis-server --appendonly yes
```

### Celery Configuration
```python
# services/shared/celery_app.py
CELERY_BROKER_URL = "redis://localhost:6379/0"
CELERY_RESULT_BACKEND = "redis://localhost:6379/0"

celery_app.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,
    task_track_started=True,
    task_time_limit=30 * 60,
    task_soft_time_limit=25 * 60,
)
```

## Running the System

### 1. Start Services
```bash
# Start all services with event system
docker-compose -f docker-compose.dev.yml up -d
```

### 2. Start Celery Workers
```bash
# Start document processing worker
celery -A services.shared.celery_app worker -Q document_queue -l info

# Start indexing worker
celery -A services.shared.celery_app worker -Q indexing_queue -l info

# Start quiz generation worker
celery -A services.shared.celery_app worker -Q quiz_queue -l info
```

### 3. Monitor Events
```bash
# Monitor Redis pub/sub
redis-cli monitor

# Monitor Celery tasks
celery -A services.shared.celery_app flower
```

## Benefits

### 1. Scalability
- **Horizontal Scaling**: Multiple workers can process tasks
- **Queue Management**: Separate queues for different task types
- **Load Distribution**: Tasks distributed across available workers

### 2. Real-time Updates
- **Instant Notifications**: Users get immediate feedback
- **Progress Tracking**: Real-time progress updates
- **Status Visibility**: Clear task status throughout the process

### 3. Reliability
- **Event Persistence**: Events stored in Redis
- **Error Handling**: Failed tasks can be retried
- **Monitoring**: Comprehensive task monitoring

### 4. Decoupling
- **Service Independence**: Services communicate via events
- **Loose Coupling**: Services don't need direct dependencies
- **Easy Extension**: New services can easily subscribe to events

## Monitoring and Debugging

### 1. Event Monitoring
```python
# Monitor all events
from services.shared import EventConsumer

def log_all_events(event):
    print(f"Event: {event.event_type} - {event.event_id}")

consumer = EventConsumer()
consumer.subscribe_to_all_events(log_all_events)
consumer.start()
```

### 2. Task Monitoring
```bash
# Monitor Celery tasks
celery -A services.shared.celery_app inspect active
celery -A services.shared.celery_app inspect stats
```

### 3. Redis Monitoring
```bash
# Monitor Redis pub/sub
redis-cli monitor | grep study_ai_events
```

## Best Practices

### 1. Event Design
- **Idempotent Events**: Events should be safe to process multiple times
- **Event Versioning**: Include version information in events
- **Event Validation**: Validate event data before processing

### 2. Error Handling
- **Dead Letter Queues**: Handle failed events
- **Retry Logic**: Implement retry mechanisms for failed tasks
- **Error Logging**: Comprehensive error logging

### 3. Performance
- **Event Batching**: Batch events when possible
- **Connection Pooling**: Use connection pools for Redis
- **Task Optimization**: Optimize task processing time

### 4. Security
- **Event Validation**: Validate all incoming events
- **Access Control**: Control access to event channels
- **Data Encryption**: Encrypt sensitive event data

## Troubleshooting

### Common Issues

1. **Events Not Published**
   - Check Redis connection
   - Verify event publisher configuration
   - Check event data validation

2. **Events Not Consumed**
   - Check event consumer subscription
   - Verify Redis pub/sub channels
   - Check event handler errors

3. **Tasks Not Processing**
   - Check Celery worker status
   - Verify queue configuration
   - Check task routing

4. **WebSocket Notifications Not Working**
   - Check WebSocket connections
   - Verify notification service
   - Check event handler implementation

### Debug Commands
```bash
# Check Redis pub/sub
redis-cli pubsub channels "study_ai_events:*"

# Check Celery queues
celery -A services.shared.celery_app inspect active_queues

# Monitor events in real-time
redis-cli subscribe "study_ai_events:*"
``` 