# Indexing Service Environment Setup

This document explains how to configure environment variables for the indexing-service.

## Quick Start

1. **Copy the example file:**
   ```bash
   cp env.example .env
   ```

2. **Edit the `.env` file** with your specific values
3. **Restart the service** to load the new configuration

## Environment Variable Categories

### 🔐 Database Configuration
- `DATABASE_URL`: PostgreSQL connection string
- Default: `postgresql://postgres:password@indexing-db:5432/indexing_db`

### 🚀 Redis Configuration
- `REDIS_URL`: Redis connection string for caching
- Default: `redis://redis:6379`

### 🌐 Service URLs
- `DOCUMENT_SERVICE_URL`: Document service endpoint
- `NOTIFICATION_SERVICE_URL`: Notification service endpoint

### 🤖 Vector Model Settings
- `EMBEDDING_MODEL`: HuggingFace model for embeddings
- `HUGGINGFACE_TOKEN`: API token for HuggingFace

### ✂️ Chunking Configuration
The service supports two chunking modes:

#### Fixed Chunking (Legacy)
- `CHUNK_MODE=FIXED`
- `CHUNK_SIZE`: Fixed character count per chunk
- `CHUNK_OVERLAP`: Overlap between chunks

#### Dynamic Chunking (LaBSE-aware) ⭐ **CURRENTLY ACTIVE**
- `CHUNK_MODE=DYNAMIC` ✅
- `CHUNK_BASE_TOKENS`: 320 ✅
- `CHUNK_MIN_TOKENS`: 180 ✅
- `CHUNK_MAX_TOKENS`: 480 ✅
- `CHUNK_SENT_OVERLAP_RATIO`: 0.12 ✅
- `LABSE_MAX_TOKENS`: 512 ✅
- `DENSITY_WEIGHT_SYMBOLS`: 0.4 ✅
- `DENSITY_WEIGHT_AVGWORD`: 0.3 ✅
- `DENSITY_WEIGHT_NUMBERS`: 0.3 ✅
- `DYNAMIC_HIERARCHY_ENABLE`: false ✅

### ⚙️ Service Configuration
- `SERVICE_NAME`: Service identifier
- `SERVICE_PORT`: HTTP server port

### 🌍 Environment Configuration
- `ENVIRONMENT`: Current environment (local, development, staging, production)
- `INFRASTRUCTURE_PROVIDER`: Cloud provider (local, aws, gcp, azure)

### 📨 Message Broker & Task Queue
- `MESSAGE_BROKER_TYPE`: Type of message broker (redis, elasticache, sqs)
- `TASK_QUEUE_TYPE`: Type of task queue (celery, sqs)

### 📝 Logging Configuration
- `LOG_LEVEL`: Log verbosity (DEBUG, INFO, WARNING, ERROR, CRITICAL)

### ☁️ AWS Configuration (for cloud deployment)
- `AWS_REGION`: AWS region
- `AWS_ACCESS_KEY_ID`: AWS access key
- `AWS_SECRET_ACCESS_KEY`: AWS secret key

### 🗄️ S3 Configuration (for cloud deployment)
- `S3_BUCKET`: S3 bucket for document storage
- `S3_REGION`: S3 region
- `S3_ACCESS_KEY_ID`: S3 access key
- `S3_SECRET_ACCESS_KEY`: S3 secret key

### 📊 Monitoring & Observability
- `CLOUDWATCH_LOG_GROUP`: CloudWatch log group
- `CLOUDWATCH_REGION`: CloudWatch region
- `XRAY_ENABLED`: Enable X-Ray tracing

## Configuration Priority

Environment variables are loaded in this order (highest to lowest priority):

1. **System Environment Variables** (`os.environ`) ✅
2. **Docker Compose Environment** (inline environment section) ✅
3. **`.env` file** (if exists in service directory)
4. **Default values** (hardcoded in `config.py`)

## Docker Compose Integration

The service automatically loads environment variables from:
- Docker Compose `environment` section ✅
- `env_file` directive (for cloud deployment)
- `.env` file in the service directory

## Current Configuration Status

### ✅ **Active Configuration**
- **Chunking Mode**: DYNAMIC (LaBSE-aware)
- **Embedding Model**: sentence-transformers/LaBSE
- **Base Tokens**: 320
- **Min/Max Tokens**: 180-480
- **Sentence Overlap Ratio**: 0.12
- **LaBSE Max Tokens**: 512

### 🔧 **Service Endpoints**
- **Health Check**: `/health` ✅
- **Configuration Debug**: `/debug-config` ✅
- **Document Indexing**: `/index` ✅
- **Vector Search**: `/search` ✅
- **Category Search**: `/search/category` ✅
- **Subject Search**: `/search/subject` ✅
- **Chunk Retrieval**: `/chunks/{document_id}` ✅
- **Statistics**: `/stats/category/{id}`, `/stats/subject/{id}` ✅

## Development vs Production

### Local Development
```bash
# Use local .env file
cp env.example .env
# Edit .env with local values
```

### Cloud Deployment
```bash
# Use cloud environment file
cp env.cloud.example env.cloud
# Edit env.cloud with production values
```

## Validation

The service validates all environment variables on startup. Check the logs for any configuration errors.

### ✅ **Current Validation Status**
- **Environment Variables**: All loaded correctly ✅
- **Configuration Overrides**: Working properly ✅
- **Service Startup**: Successful ✅
- **API Endpoints**: All functional ✅

## Troubleshooting

### Common Issues
1. **Missing .env file**: Copy from `env.example`
2. **Invalid database URL**: Check PostgreSQL connection
3. **Redis connection failed**: Verify Redis service is running
4. **Chunking errors**: Ensure chunking parameters are valid

### Debug Mode
Set `LOG_LEVEL=DEBUG` to see detailed configuration loading information.

### Configuration Verification
Use the `/debug-config` endpoint to verify current configuration values:
```bash
curl http://localhost:8003/debug-config | jq .
```

## Security Notes

- **Never commit `.env` files** to version control
- **Use strong passwords** for production databases
- **Rotate API keys** regularly
- **Use IAM roles** instead of access keys in AWS when possible

## Recent Updates

### ✅ **Completed**
- **Test endpoints removed**: `/test-index` and `/test-dynamic-chunking` removed
- **Environment variables**: All properly loaded from Docker Compose
- **Configuration**: DYNAMIC chunking mode active
- **API cleanup**: Production endpoints only

### 🔄 **Current Status**
- **Service**: Fully operational with DYNAMIC chunking
- **Configuration**: All environment variables loaded correctly
- **Endpoints**: Clean, production-ready API
- **Documentation**: Updated to reflect current state
