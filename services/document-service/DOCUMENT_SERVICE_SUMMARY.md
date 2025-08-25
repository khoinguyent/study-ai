# Document Service Summary

## Overview
The Document Service is a core microservice in the Study AI platform that handles document upload, storage, processing, and management. It provides a RESTful API for managing subjects, categories, and documents with event-driven architecture for asynchronous processing.

## Architecture

### Core Components
- **FastAPI Application** (`main.py`) - Main REST API server
- **SQLAlchemy Models** (`models.py`) - Database schema definitions
- **Pydantic Schemas** (`schemas.py`) - API request/response models
- **Celery Tasks** (`tasks.py`) - Asynchronous task processing
- **Event System** (`shared/events.py`) - Event-driven communication
- **Storage Service** (`storage_service.py`) - MinIO/S3 file storage
- **Document Processor** (`document_processor.py`) - Document processing logic

### Database Models
- **Subject**: Top-level organization unit (e.g., "History", "Science")
  - Fields: id, name, description, icon, color_theme, user_id, timestamps
  - Has many categories and documents
  
- **Category**: Sub-organization within subjects (e.g., "Vietnam History", "Chemistry")
  - Fields: id, name, description, subject_id, user_id, timestamps
  - Belongs to one subject, has many documents
  
- **Document**: Individual files uploaded by users
  - Fields: id, filename, content_type, file_size, file_path, status, user_id, subject_id, category_id, timestamps
  - Belongs to optional subject/category, has processing status

### API Endpoints

#### Subjects
- `POST /subjects` - Create new subject
- `GET /subjects` - List user's subjects
- `GET /subjects/{subject_id}` - Get subject details
- `PUT /subjects/{subject_id}` - Update subject
- `DELETE /subjects/{subject_id}` - Delete subject

#### Categories
- `POST /categories` - Create new category
- `GET /categories` - List categories for a subject
- `GET /categories/{category_id}` - Get category details
- `PUT /categories/{category_id}` - Update category
- `DELETE /categories/{category_id}` - Delete category

#### Documents
- `POST /documents/upload` - Upload new document
- `GET /documents` - List user's documents (with pagination)
- `GET /documents/{document_id}` - Get document details
- `PUT /documents/{document_id}` - Update document metadata
- `DELETE /documents/{document_id}` - Delete document
- `GET /documents/grouped` - Get documents grouped by subject/category

#### System
- `GET /health` - Service health check
- `GET /supported-formats` - List supported document formats
- `POST /extract-pdf-text` - Extract text from PDF with quality assessment

## Key Features

### Document Processing Pipeline
1. **Upload**: File uploaded via API, stored in MinIO
2. **Processing**: Asynchronous processing via Celery tasks
3. **Text Extraction**: Extract text from various file formats (PDF, DOCX, DOC, Excel, etc.)
4. **Chunking**: Split document into smaller pieces for indexing
5. **Indexing**: Trigger indexing service for vector search
6. **Status Updates**: Real-time progress updates via notifications

### Text Extraction Capabilities

The service now includes a comprehensive text extraction service:

1. **DOCX Files**: Full text extraction using python-docx library
   - Extracts text from paragraphs and tables
   - Preserves document structure
   - Extracts metadata (paragraph count, table count, headers, footers)
   
2. **DOC Files**: Basic text extraction for legacy Word documents
   - Note: Limited functionality, consider using antiword for better results
   
3. **PDF Files**: Enhanced text extraction using PyPDF2
   - Multi-page support with quality assessment
   - Page-by-page text extraction with metadata
   - Advanced text cleaning and artifact removal
   - Quality scoring and improvement recommendations
   - OCR and alternative processing suggestions
   
4. **Excel Files**: Text extraction using pandas
   - Multi-sheet support
   - Table data extraction
   - Metadata (sheet count, row count)
   
5. **Plain Text**: Multiple encoding support
   - UTF-8, Latin-1, CP1252, ISO-8859-1
   - Automatic encoding detection

### File Storage
- **MinIO Integration**: S3-compatible object storage
- **File Organization**: Structured storage by user_id/document_id
- **Content Types**: Supports PDF, DOCX, DOC, Excel, and text files
- **Presigned URLs**: Secure file access with expiration

### Event-Driven Architecture
- **Event Types**: Document lifecycle events (upload, processing, completion, failure)
- **Event Publishing**: Async event publishing for service communication
- **Task Status Updates**: Real-time progress tracking
- **Dead Letter Queue**: Failed event handling and retry mechanisms

### Authentication & Security
- **JWT Verification**: Integration with auth service
- **User Isolation**: All operations scoped to authenticated user
- **CORS Support**: Configurable cross-origin resource sharing

## Configuration

### Environment Variables
```bash
# Database
DATABASE_URL=postgresql://postgres:password@document-db:5432/document_db

# Redis
REDIS_URL=redis://redis:6379

# MinIO Storage
MINIO_ENDPOINT=minio:9000
MINIO_ACCESS_KEY=minioadmin
MINIO_SECRET_KEY=minioadmin
MINIO_BUCKET=study-ai-documents
MINIO_SECURE=false

# Service URLs
AUTH_SERVICE_URL=http://auth-service:8001
INDEXING_SERVICE_URL=http://indexing-service:8003
NOTIFICATION_SERVICE_URL=http://notification-service:8005
```

### Dependencies
- **FastAPI**: Web framework
- **SQLAlchemy**: ORM and database management
- **Celery**: Asynchronous task processing
- **MinIO**: Object storage client
- **Alembic**: Database migrations
- **Pydantic**: Data validation and serialization

## Deployment

### Docker
- **Base Image**: Python 3.11-slim
- **Port**: 8002
- **Health Check**: HTTP endpoint monitoring
- **Non-root User**: Security best practices

### Service Dependencies
- **PostgreSQL**: Primary database
- **Redis**: Celery broker and caching
- **MinIO**: Object storage
- **Auth Service**: JWT verification
- **Indexing Service**: Document indexing
- **Notification Service**: User notifications

## Development Workflow

### Database Migrations
```bash
# Create new migration
alembic revision --autogenerate -m "description"

# Apply migrations
alembic upgrade head

# Rollback
alembic downgrade -1
```

### Testing
- **Unit Tests**: pytest framework
- **Async Support**: pytest-asyncio
- **Test Data**: Seed scripts for development

### Local Development
```bash
# Install dependencies
pip install -r requirements.txt

# Run migrations
alembic upgrade head

# Start service
uvicorn app.main:app --reload --port 8002

# Start Celery worker
celery -A app.celery_app worker --loglevel=info
```

## Integration Points

### External Services
- **Auth Service**: User authentication and JWT verification
- **Indexing Service**: Document vectorization and search indexing
- **Notification Service**: User notifications and task status updates

### Event Consumers
- **Quiz Service**: Document processing completion events
- **Indexing Service**: Document upload and processing events
- **Notification Service**: Task status and progress events

## Monitoring & Observability

### Health Checks
- **HTTP Endpoint**: `/health` for service status
- **Database Connectivity**: Connection verification
- **Storage Service**: MinIO connectivity check

### Logging
- **Structured Logging**: Consistent log format
- **Error Tracking**: Exception handling and logging
- **Performance Metrics**: Processing time tracking

### Task Monitoring
- **Celery Flower**: Task queue monitoring
- **Progress Tracking**: Real-time task status updates
- **Failure Handling**: Error logging and retry mechanisms

## Common Use Cases

### Document Upload Flow
1. User uploads document via web interface
2. Document metadata stored in database
3. File uploaded to MinIO storage
4. Celery task triggered for processing
5. Document processed and indexed
6. User notified of completion

### Subject Organization
1. User creates subject (e.g., "History")
2. User creates categories within subject (e.g., "Vietnam History")
3. Documents uploaded and assigned to categories
4. Hierarchical organization for easy navigation

### Batch Processing
1. Multiple documents uploaded simultaneously
2. Parallel processing via Celery workers
3. Progress tracking for each document
4. Bulk status updates and notifications

## Troubleshooting

### Common Issues
- **Database Connection**: Check DATABASE_URL and PostgreSQL status
- **Storage Issues**: Verify MinIO connectivity and bucket permissions
- **Task Failures**: Check Celery worker logs and Redis connectivity
- **Event Publishing**: Verify event broker configuration

### Debug Commands
```bash
# Check service health
curl http://localhost:8002/health

# View Celery tasks
celery -A app.celery_app inspect active

# Check MinIO connectivity
curl http://minio:9000/minio/health/live

# Database connection test
python -c "from app.database import get_db; next(get_db())"
```

## Future Enhancements

### Planned Features
- **Document Versioning**: Track document changes over time
- **Advanced Search**: Full-text search within documents
- **Document Collaboration**: Multi-user editing and commenting
- **Format Conversion**: Automatic format conversion (PDF to DOCX, etc.)
- **OCR Support**: Image-based document text extraction

### Performance Optimizations
- **Caching Layer**: Redis-based document metadata caching
- **Async Processing**: Improved async/await patterns
- **Batch Operations**: Bulk document operations
- **CDN Integration**: Content delivery network for file access

## Related Documentation
- [Database Schema](../docs/DATABASE_SCHEMA.md)
- [Event-Driven Architecture](../docs/EVENT_DRIVEN_ARCHITECTURE.md)
- [Infrastructure Architecture](../../INFRASTRUCTURE_ARCHITECTURE.md)
- [API Documentation](../postman/Study-AI-API-Collection.json)
