# Study AI Backend API Documentation

## Base URL
- Local Development: `http://localhost/api`
- Production: `https://your-domain.com/api`

## Authentication
Currently, the API uses simple user ID-based authentication. In production, implement proper JWT authentication.

## API Endpoints

### Health Check
#### GET `/`
Check if the service is running.

**Response:**
```json
{
  "status": "healthy",
  "message": "Study AI Backend is running",
  "version": "1.0.0"
}
```

#### GET `/api/health`
Check the health of all services.

**Response:**
```json
{
  "status": "ok",
  "services": {
    "web": "running",
    "database": "connected",
    "redis": "connected",
    "celery": "running"
  }
}
```

### User Management

#### POST `/api/users`
Create a new user.

**Request Body:**
```json
{
  "email": "user@example.com",
  "name": "John Doe"
}
```

**Response:**
```json
{
  "message": "User created successfully",
  "user": {
    "id": "uuid-string",
    "email": "user@example.com",
    "name": "John Doe"
  }
}
```

#### GET `/api/users/{user_id}`
Get user information.

**Response:**
```json
{
  "user": {
    "id": "uuid-string",
    "email": "user@example.com",
    "name": "John Doe",
    "created_at": "2024-01-01T00:00:00Z"
  }
}
```

### Document Management

#### POST `/api/upload`
Upload a document for processing.

**Request:**
- Method: `POST`
- Content-Type: `multipart/form-data`
- Body:
  - `file`: The document file (PDF, DOC, DOCX, TXT, PPT, PPTX)
  - `user_id`: User ID

**Response:**
```json
{
  "message": "File uploaded successfully",
  "document_id": "uuid-string",
  "filename": "document.pdf",
  "task_id": "celery-task-id",
  "status": "processing"
}
```

#### GET `/api/documents/{document_id}`
Get document information.

**Response:**
```json
{
  "document": {
    "id": "uuid-string",
    "filename": "document.pdf",
    "file_size": 1024000,
    "file_type": "pdf",
    "status": "completed",
    "created_at": "2024-01-01T00:00:00Z",
    "chunks_count": 25
  }
}
```

#### GET `/api/users/{user_id}/documents`
Get all documents for a user.

**Response:**
```json
{
  "documents": [
    {
      "id": "uuid-string",
      "filename": "document.pdf",
      "file_size": 1024000,
      "file_type": "pdf",
      "status": "completed",
      "created_at": "2024-01-01T00:00:00Z",
      "chunks_count": 25
    }
  ]
}
```

### Quiz Generation

#### POST `/api/quizzes`
Create a new quiz from selected documents.

**Request Body:**
```json
{
  "document_ids": ["uuid-1", "uuid-2"],
  "user_id": "user-uuid",
  "num_questions": 10
}
```

**Response:**
```json
{
  "message": "Quiz generation started",
  "quiz_id": "uuid-string",
  "task_id": "celery-task-id",
  "status": "generating"
}
```

#### GET `/api/quizzes/{quiz_id}`
Get quiz information.

**Response:**
```json
{
  "quiz": {
    "id": "uuid-string",
    "title": "Quiz from 2 document(s)",
    "description": "Generated quiz covering 5 topics",
    "status": "completed",
    "topics": ["Cell Structure", "Photosynthesis", "DNA Replication"],
    "questions": [
      {
        "question": "What is the main function of mitochondria?",
        "options": {
          "A": "Energy production",
          "B": "Protein synthesis",
          "C": "DNA replication",
          "D": "Cell division"
        },
        "correct_answer": "A",
        "explanation": "Mitochondria are the powerhouse of the cell, responsible for energy production through cellular respiration.",
        "difficulty": "medium",
        "topic": "Cell Structure"
      }
    ],
    "total_questions": 10,
    "created_at": "2024-01-01T00:00:00Z"
  }
}
```

#### GET `/api/users/{user_id}/quizzes`
Get all quizzes for a user.

**Response:**
```json
{
  "quizzes": [
    {
      "id": "uuid-string",
      "title": "Quiz from 2 document(s)",
      "status": "completed",
      "total_questions": 10,
      "created_at": "2024-01-01T00:00:00Z"
    }
  ]
}
```

### Task Management

#### GET `/api/tasks/{task_id}`
Get task status.

**Response:**
```json
{
  "task_id": "celery-task-id",
  "status": "SUCCESS",
  "result": {
    "status": "completed",
    "document_id": "uuid-string",
    "chunks_processed": 25
  }
}
```

## Error Responses

All endpoints may return the following error responses:

### 400 Bad Request
```json
{
  "error": "Error description"
}
```

### 404 Not Found
```json
{
  "error": "Resource not found"
}
```

### 409 Conflict
```json
{
  "error": "Resource already exists"
}
```

### 500 Internal Server Error
```json
{
  "error": "Internal server error"
}
```

## File Upload Guidelines

### Supported File Types
- PDF (.pdf)
- Microsoft Word (.doc, .docx)
- Plain Text (.txt)
- Microsoft PowerPoint (.ppt, .pptx)

### File Size Limits
- Maximum file size: 100MB

### Processing Status
Documents go through the following statuses:
1. `uploaded` - File uploaded to S3
2. `processing` - Document being processed by Celery worker
3. `completed` - Processing finished successfully
4. `failed` - Processing failed

## Background Processing

### Document Processing
1. File uploaded to S3
2. Celery worker downloads file
3. Text extraction and chunking
4. Embedding generation using OpenAI
5. Storage in PostgreSQL with pgvector

### Quiz Generation
1. Topic extraction from document chunks
2. Context retrieval using vector similarity
3. Question generation using AI agents
4. Quiz compilation and storage

## Rate Limiting

- API endpoints: 10 requests per second
- File uploads: 1 request per second
- Rate limits are enforced by Nginx

## Development Notes

### Local Development
1. Set up environment variables in `.env` file
2. Ensure PostgreSQL with pgvector extension is running
3. Ensure Redis is running
4. Start Celery workers: `celery -A app.celery worker --loglevel=info`
5. Start Celery beat: `celery -A app.celery beat --loglevel=info`

### Testing
Use the provided `test-api.sh` script to test all endpoints:
```bash
./test-api.sh
```

### Monitoring
- Check Celery task status via `/api/tasks/{task_id}`
- Monitor service health via `/api/health`
- View application logs for debugging 