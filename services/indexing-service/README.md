# Indexing Service

The indexing service provides intelligent document chunking and vector-based search capabilities for the Study AI platform.

## 🚀 **Quick Start**

### Start the Service
```bash
# Start all services
docker-compose up --build

# Start only indexing service
docker-compose up indexing-service
```

### Health Check
```bash
curl http://localhost:8003/health
```

### Check Configuration
```bash
curl http://localhost:8003/debug-config | jq .
```

## 🏗️ **Architecture**

### Core Components
- **Document Processor**: Handles document ingestion and text extraction
- **Chunking Engine**: Intelligent document segmentation
- **Vector Service**: Embedding generation and similarity search
- **Database Layer**: PostgreSQL with pgvector extension
- **Cache Layer**: Redis for performance optimization

### Chunking Strategies

#### Dynamic Chunking (LaBSE-aware) ⭐ **ACTIVE**
- **Mode**: `CHUNK_MODE=DYNAMIC`
- **Base Tokens**: 320
- **Min/Max Tokens**: 180-480
- **Sentence Overlap Ratio**: 0.12
- **LaBSE Max Tokens**: 512
- **Density Weights**: 
  - Symbols: 0.4
  - Average Words: 0.3
  - Numbers: 0.3

#### Fixed Chunking (Legacy)
- **Mode**: `CHUNK_MODE=FIXED`
- **Chunk Size**: 1000 characters
- **Overlap**: 200 characters

### Vector Model
- **Embedding Model**: `sentence-transformers/LaBSE`
- **Dimensions**: 384
- **Language Support**: Multi-language (LaBSE)
- **Performance**: Optimized for semantic similarity

## 🔧 **API Endpoints**

### Health & Configuration
| Endpoint | Method | Description |
|----------|--------|-------------|
| `/health` | GET | Service health check |
| `/debug-config` | GET | Current configuration values |

### Document Processing
| Endpoint | Method | Description |
|----------|--------|-------------|
| `/index` | POST | Process and index documents |

### Search & Retrieval
| Endpoint | Method | Description |
|----------|--------|-------------|
| `/search` | POST | Vector similarity search |
| `/search/category` | POST | Category-based search |
| `/search/subject` | POST | Subject-based search |

### Chunk Management
| Endpoint | Method | Description |
|----------|--------|-------------|
| `/chunks/{document_id}` | GET | Retrieve chunks by document |
| `/chunks/category/{category_id}` | GET | Retrieve chunks by category |
| `/chunks/subject/{subject_id}` | GET | Retrieve chunks by subject |

### Statistics
| Endpoint | Method | Description |
|----------|--------|-------------|
| `/stats/category/{category_id}` | GET | Category usage statistics |
| `/stats/subject/{subject_id}` | GET | Subject usage statistics |

## 📝 **API Examples**

### Document Indexing
```bash
curl -X POST "http://localhost:8003/index" \
  -H "Content-Type: application/json" \
  -d '{
    "document_id": "doc-123",
    "content": "Document content here...",
    "subject_id": "subject-456",
    "category_id": "category-789"
  }'
```

### Vector Search
```bash
curl -X POST "http://localhost:8003/search" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "machine learning algorithms",
    "limit": 10
  }'
```

### Category Search
```bash
curl -X POST "http://localhost:8003/search/category" \
  -H "Content-Type: application/json" \
  -d '{
    "category_id": "category-789",
    "query": "artificial intelligence",
    "limit": 5
  }'
```

## ⚙️ **Configuration**

### Environment Variables
All configuration is loaded from Docker Compose environment variables:

```yaml
environment:
  # Database
  DATABASE_URL: postgresql://postgres:password@indexing-db:5432/indexing_db
  
  # Redis
  REDIS_URL: redis://redis:6379
  
  # Service URLs
  DOCUMENT_SERVICE_URL: http://document-service:8002
  NOTIFICATION_SERVICE_URL: http://notification-service:8005
  
  # Chunking Configuration
  CHUNK_MODE: DYNAMIC
  CHUNK_BASE_TOKENS: 320
  CHUNK_MIN_TOKENS: 180
  CHUNK_MAX_TOKENS: 480
  CHUNK_SENT_OVERLAP_RATIO: 0.12
  LABSE_MAX_TOKENS: 512
  DENSITY_WEIGHT_SYMBOLS: 0.4
  DENSITY_WEIGHT_AVGWORD: 0.3
  DENSITY_WEIGHT_NUMBERS: 0.3
  DYNAMIC_HIERARCHY_ENABLE: "false"
  
  # Vector Model
  EMBEDDING_MODEL: sentence-transformers/LaBSE
  HUGGINGFACE_TOKEN: ""
  
  # Service
  SERVICE_NAME: indexing-service
  SERVICE_PORT: 8003
```

### Configuration Priority
1. **System Environment Variables** (highest priority)
2. **Docker Compose Environment** (inline environment section)
3. **`.env` file** (if exists in service directory)
4. **Default values** (hardcoded in `config.py`)

## 🗄️ **Database Schema**

### DocumentChunks Table
```sql
CREATE TABLE document_chunks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    document_id VARCHAR NOT NULL,
    subject_id VARCHAR NOT NULL,
    category_id VARCHAR NOT NULL,
    content TEXT NOT NULL,
    embedding vector(384),
    chunk_index INTEGER NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for performance
CREATE INDEX idx_document_chunks_document_id ON document_chunks(document_id);
CREATE INDEX idx_document_chunks_subject_id ON document_chunks(subject_id);
CREATE INDEX idx_document_chunks_category_id ON document_chunks(category_id);
CREATE INDEX idx_document_chunks_embedding ON document_chunks USING ivfflat (embedding vector_cosine_ops);
```

## 🔍 **Search Algorithms**

### Vector Similarity Search
- **Algorithm**: Cosine similarity with pgvector
- **Index Type**: IVFFlat for approximate nearest neighbor search
- **Performance**: Optimized for large-scale similarity queries

### Chunking Algorithm
- **Dynamic Mode**: LaBSE-aware semantic chunking
- **Sentence Boundary Detection**: Intelligent sentence splitting
- **Density Analysis**: Content-aware chunk sizing
- **Overlap Management**: Configurable sentence overlap ratios

## 📊 **Performance & Monitoring**

### Health Checks
- **Service Health**: `/health` endpoint
- **Database Connectivity**: PostgreSQL connection monitoring
- **Redis Connectivity**: Cache layer monitoring
- **Vector Model**: Embedding generation health

### Metrics
- **Chunking Performance**: Documents processed per second
- **Search Latency**: Query response times
- **Memory Usage**: Embedding model memory consumption
- **Database Performance**: Query execution times

## 🚀 **Development**

### Local Development
```bash
# Clone the repository
git clone <repository-url>
cd services/indexing-service

# Install dependencies
pip install -r requirements.txt

# Set up environment
cp env.example .env
# Edit .env with local values

# Run the service
python -m uvicorn app.main:app --host 0.0.0.0 --port 8003 --reload
```

### Testing
```bash
# Run tests
pytest

# Run with coverage
pytest --cov=app --cov-report=html
```

### Docker Development
```bash
# Build and run
docker-compose up --build indexing-service

# View logs
docker-compose logs -f indexing-service

# Execute commands
docker-compose exec indexing-service bash
```

## 🔧 **Troubleshooting**

### Common Issues

#### Environment Variables Not Loading
```bash
# Check current configuration
curl http://localhost:8003/debug-config

# Verify Docker environment
docker-compose exec indexing-service env | grep CHUNK_MODE
```

#### Database Connection Issues
```bash
# Check database health
docker-compose ps indexing-db

# Test connection
docker-compose exec indexing-service python -c "
from app.database import get_db
print('Database connection test')
"
```

#### Vector Model Issues
```bash
# Check model loading
docker-compose logs indexing-service | grep -i "embedding\|model"

# Verify HuggingFace token
docker-compose exec indexing-service env | grep HUGGINGFACE_TOKEN
```

### Debug Mode
```bash
# Set debug logging
export LOG_LEVEL=DEBUG

# Restart service
docker-compose restart indexing-service
```

## 📚 **Dependencies**

### Core Dependencies
- **FastAPI**: Web framework
- **SQLAlchemy**: Database ORM
- **pgvector**: Vector similarity search
- **Redis**: Caching and message broker
- **sentence-transformers**: Embedding generation

### Development Dependencies
- **pytest**: Testing framework
- **pytest-asyncio**: Async testing support
- **httpx**: HTTP client for testing

## 🎯 **Current Status**

### ✅ **Completed Features**
- **Dynamic Chunking**: LaBSE-aware intelligent chunking
- **Vector Search**: High-performance similarity search
- **API Endpoints**: Complete REST API
- **Configuration Management**: Environment variable support
- **Database Integration**: PostgreSQL with pgvector
- **Health Monitoring**: Service health checks
- **Production Ready**: Clean, tested codebase

### 🔄 **Active Development**
- **Performance Optimization**: Query optimization
- **Monitoring**: Enhanced metrics collection
- **Documentation**: API documentation updates

### 🚧 **Future Enhancements**
- **Advanced Chunking**: Hierarchical document analysis
- **Multi-language Support**: Enhanced language detection
- **Real-time Indexing**: Streaming document processing
- **Advanced Search**: Semantic search with filters

## 📞 **Support**

For issues and questions:
1. Check the troubleshooting section
2. Review service logs: `docker-compose logs indexing-service`
3. Verify configuration: `curl http://localhost:8003/debug-config`
4. Check service health: `curl http://localhost:8003/health`

---

The indexing service is now **production-ready** with intelligent document chunking, vector search capabilities, and comprehensive configuration management! 🎉
