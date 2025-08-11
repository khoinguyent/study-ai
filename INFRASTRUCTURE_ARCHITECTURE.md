# Study AI Platform - Infrastructure Architecture

## Overview

The Study AI Platform now supports both local and cloud environments using a flexible infrastructure abstraction layer. This architecture allows seamless switching between local development (Redis + Celery) and cloud production (ElastiCache + SQS) without code changes.

## Architecture Design Patterns

### 1. Strategy Pattern
- **Message Broker Strategy**: Redis (local) vs ElastiCache (cloud)
- **Task Queue Strategy**: Celery (local) vs SQS (cloud)
- **Storage Strategy**: MinIO (local) vs S3 (cloud)

### 2. Factory Pattern
- **InfrastructureFactory**: Creates appropriate infrastructure components based on environment
- **Dynamic Component Creation**: Automatically selects Redis/ElastiCache, Celery/SQS based on configuration

### 3. Abstract Factory Pattern
- **InfrastructureConfig**: Centralized configuration management
- **Environment Detection**: Automatic environment detection and configuration

## Environment Configuration

### Local Environment
```bash
# Copy and configure local environment
cp env.local.example .env.local

# Key settings for local development
ENVIRONMENT=local
INFRASTRUCTURE_PROVIDER=local
MESSAGE_BROKER_TYPE=redis
TASK_QUEUE_TYPE=celery
```

### Cloud Environment
```bash
# Copy and configure cloud environment
cp env.cloud.example .env.cloud

# Key settings for cloud deployment
ENVIRONMENT=cloud
INFRASTRUCTURE_PROVIDER=aws
MESSAGE_BROKER_TYPE=elasticache
TASK_QUEUE_TYPE=sqs
```

## Infrastructure Components

### Message Brokers

#### Redis (Local)
- **Purpose**: Pub/sub messaging for events
- **Configuration**: `redis://redis:6379`
- **Features**: Real-time event broadcasting, caching

#### ElastiCache (Cloud)
- **Purpose**: Managed Redis service on AWS
- **Configuration**: `redis://your-elasticache-endpoint:6379`
- **Features**: High availability, automatic failover, scaling

### Task Queues

#### Celery (Local)
- **Purpose**: Background task processing
- **Configuration**: Uses Redis as broker and backend
- **Features**: Task scheduling, retries, monitoring

#### SQS (Cloud)
- **Purpose**: Managed message queuing on AWS
- **Configuration**: `https://sqs.region.amazonaws.com/account/queue`
- **Features**: Guaranteed delivery, dead letter queues, scaling

## Usage Examples

### 1. Basic Infrastructure Usage

```python
from services.shared.infrastructure import (
    get_message_broker, 
    get_task_queue, 
    is_local_environment
)

# Get configured message broker (Redis or ElastiCache)
message_broker = get_message_broker()
message_broker.connect()

# Publish an event
success = message_broker.publish("channel_name", "message_data")

# Get configured task queue (Celery or SQS)
task_queue = get_task_queue()
task_queue.connect()

# Enqueue a task
task_id = task_queue.enqueue("task_name", args=("arg1",), kwargs={"key": "value"})
```

### 2. Event Publishing

```python
from services.shared.event_publisher import EventPublisher

# Create event publisher (automatically uses infrastructure abstraction)
publisher = EventPublisher()

# Publish events (works with both Redis and ElastiCache)
publisher.publish_document_uploaded(
    user_id="user123",
    document_id="doc456",
    filename="document.pdf",
    file_size=1024000,
    content_type="application/pdf"
)
```

### 3. Event Consumption

```python
from services.shared.event_consumer import EventConsumer

# Create event consumer (automatically uses infrastructure abstraction)
consumer = EventConsumer()

# Subscribe to events
def handle_document_event(event):
    print(f"Document event: {event.event_type}")

consumer.subscribe_to_document_events(handle_document_event)
consumer.start()
```

### 4. Task Enqueuing

```python
from services.shared.celery_app import enqueue_task

# Enqueue task (automatically uses Celery or SQS)
task_id = enqueue_task(
    task_name="app.tasks.process_document",
    args=("document_id",),
    kwargs={"user_id": "user123"}
)
```

## Deployment

### Local Development
```bash
# Start local environment with Redis and Celery
docker-compose up -d

# Start Celery workers
celery -A services.shared.celery_app worker -Q document_queue -l info
celery -A services.shared.celery_app worker -Q indexing_queue -l info
celery -A services.shared.celery_app worker -Q quiz_queue -l info
```

### Cloud Deployment
```bash
# Deploy to cloud environment
./deploy-cloud.sh

# Or manually with docker-compose
docker-compose -f docker-compose.cloud.yml up -d
```

## Configuration Management

### Environment Variables

| Variable | Local | Cloud | Description |
|----------|-------|-------|-------------|
| `ENVIRONMENT` | `local` | `cloud` | Environment type |
| `INFRASTRUCTURE_PROVIDER` | `local` | `aws` | Infrastructure provider |
| `MESSAGE_BROKER_TYPE` | `redis` | `elasticache` | Message broker type |
| `TASK_QUEUE_TYPE` | `celery` | `sqs` | Task queue type |
| `REDIS_HOST` | `redis` | `elasticache-endpoint` | Redis/ElastiCache host |
| `AWS_REGION` | - | `us-east-1` | AWS region |
| `AWS_ACCESS_KEY_ID` | - | `your-key` | AWS access key |
| `AWS_SECRET_ACCESS_KEY` | - | `your-secret` | AWS secret key |

### Service Configuration

Each service automatically detects the environment and configures itself accordingly:

```python
# services/shared/infrastructure.py
def get_redis_url() -> str:
    """Get Redis URL for backward compatibility"""
    return infra_config.get_message_broker_url()
```

## Migration Guide

### From Local to Cloud

1. **Update Environment Configuration**
   ```bash
   cp env.cloud.example env.cloud
   # Edit env.cloud with your AWS credentials and endpoints
   ```

2. **Deploy Infrastructure**
   ```bash
   # Deploy AWS infrastructure (ElastiCache, SQS, RDS, etc.)
   cd study-ai-aws-infra
   make deploy
   ```

3. **Deploy Services**
   ```bash
   # Deploy services to cloud
   ./deploy-cloud.sh
   ```

### From Cloud to Local

1. **Update Environment Configuration**
   ```bash
   cp env.local.example .env.local
   # Edit .env.local with local settings
   ```

2. **Start Local Services**
   ```bash
   docker-compose up -d
   ```

## Monitoring and Debugging

### Local Environment
```bash
# View service logs
docker-compose logs -f

# Monitor Redis
redis-cli monitor

# Monitor Celery
celery -A services.shared.celery_app flower
```

### Cloud Environment
```bash
# View service logs
docker-compose -f docker-compose.cloud.yml logs -f

# Monitor ElastiCache
aws elasticache describe-cache-clusters

# Monitor SQS
aws sqs get-queue-attributes --queue-url $SQS_QUEUE_URL
```

## Benefits

### 1. **Code Consistency**
- Same codebase works in both environments
- No conditional logic for infrastructure differences
- Consistent API across environments

### 2. **Easy Migration**
- Seamless transition from local to cloud
- Gradual migration possible
- Rollback capability

### 3. **Scalability**
- Cloud-native services for production
- Local services for development
- Automatic scaling in cloud

### 4. **Cost Optimization**
- Use local resources for development
- Pay-per-use cloud services for production
- No unnecessary cloud costs during development

## Future Enhancements

### 1. **Additional Cloud Providers**
- Google Cloud Platform (Cloud Memorystore, Cloud Tasks)
- Microsoft Azure (Azure Cache for Redis, Azure Service Bus)
- Multi-cloud support

### 2. **Advanced Features**
- Circuit breakers for cloud services
- Automatic retry with exponential backoff
- Health check integration
- Metrics and observability

### 3. **Infrastructure as Code**
- Terraform modules for cloud resources
- Automated infrastructure provisioning
- Environment-specific configurations

## Troubleshooting

### Common Issues

1. **Connection Failures**
   - Check environment variables
   - Verify network connectivity
   - Check AWS credentials

2. **Task Processing Issues**
   - Verify task queue configuration
   - Check worker status
   - Review task logs

3. **Event Publishing Issues**
   - Verify message broker connection
   - Check channel subscriptions
   - Review event logs

### Debug Commands

```bash
# Check infrastructure configuration
python -c "from services.shared.infrastructure import infra_config; print(infra_config.__dict__)"

# Test message broker connection
python -c "from services.shared.infrastructure import get_message_broker; broker = get_message_broker(); print(broker.connect())"

# Test task queue connection
python -c "from services.shared.infrastructure import get_task_queue; queue = get_task_queue(); print(queue.connect())"
```

## Contributing

When adding new infrastructure components:

1. **Extend the Abstract Base Classes**
   - Add new methods to `MessageBroker` or `TaskQueue`
   - Implement in concrete classes

2. **Update the Factory**
   - Add new component types to enums
   - Update factory methods

3. **Add Configuration Options**
   - Extend `InfrastructureConfig`
   - Add environment variables

4. **Update Documentation**
   - Document new features
   - Add usage examples

## Support

For issues or questions:

1. Check the troubleshooting section
2. Review service logs
3. Verify environment configuration
4. Check infrastructure connectivity
5. Review AWS service status (for cloud deployments)
