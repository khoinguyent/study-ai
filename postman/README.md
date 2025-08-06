# Study AI - Postman API Collection

This directory contains a comprehensive Postman collection for testing all Study AI platform APIs.

## 📁 Files

- **`Study-AI-API-Collection.json`** - Complete API collection with all endpoints
- **`Study-AI-Environment.json`** - Environment variables for development
- **`README.md`** - This documentation file

## 🚀 Quick Start

### 1. Import Collection and Environment

1. **Open Postman**
2. **Import Collection:**
   - Click "Import" → Select `Study-AI-API-Collection.json`
3. **Import Environment:**
   - Click "Import" → Select `Study-AI-Environment.json`
4. **Select Environment:**
   - Choose "Study AI - Development Environment" from the dropdown

### 2. Start Your Development Environment

```bash
# Start all services
./scripts/setup-dev.sh

# Or manually
docker-compose -f docker-compose.dev.yml up -d
```

### 3. Test Authentication

1. **Run "Login User"** from the Auth Service folder
2. **Check the response** - you should get an access token
3. **The token is automatically saved** to the `auth_token` variable

## 📋 API Endpoints Overview

### 🔐 Auth Service
- **Health Check** - Verify service is running
- **Register User** - Create new user account
- **Login User** - Authenticate and get JWT token
- **Get Current User** - Get user profile (requires auth)
- **Verify Token** - Validate JWT token

### 📄 Document Service
- **Health Check** - Verify service is running
- **Upload Document** - Upload file (PDF, DOCX, XLSX, TXT)
- **List Documents** - Get user's documents (requires auth)
- **Get Document** - Get specific document details (requires auth)
- **Delete Document** - Remove document (requires auth)

### 🔍 Indexing Service
- **Health Check** - Verify service is running
- **Index Document** - Process document for search
- **Search Documents** - Find relevant content
- **Get Document Chunks** - Get processed chunks
- **Delete Document Chunks** - Remove indexed data

### 🧠 Quiz Service
- **Health Check** - Verify service is running
- **Generate Quiz** - Create AI-powered quiz (requires auth)
- **List Quizzes** - Get user's quizzes (requires auth)
- **Get Quiz** - Get specific quiz details (requires auth)
- **Delete Quiz** - Remove quiz (requires auth)

### 🔔 Notification Service
- **Health Check** - Verify service is running
- **Create Task Status** - Create task tracking
- **Update Task Status** - Update task progress
- **Get Task Status** - Get task details
- **Get User Task Statuses** - List user's tasks
- **Create Notification** - Send notification
- **Get User Notifications** - List user's notifications
- **Mark Notification as Read** - Update notification status

### 🛠️ Development Tools
- **Test Ollama** - Test local LLM
- **List Ollama Models** - Check available models

## 🔄 Testing Workflow

### Complete User Journey

1. **Authentication:**
   ```
   Login User → Get Current User → Verify Token
   ```

2. **Document Management:**
   ```
   Upload Document → List Documents → Get Document
   ```

3. **Content Processing:**
   ```
   Index Document → Search Documents → Get Document Chunks
   ```

4. **Quiz Generation:**
   ```
   Generate Quiz → List Quizzes → Get Quiz
   ```

5. **Task Monitoring:**
   ```
   Create Task Status → Update Task Status → Get Task Status
   ```

## 🔧 Environment Variables

### Core Variables
- `base_url` - API Gateway URL (http://localhost:8000)
- `auth_token` - JWT authentication token (auto-populated)
- `user_id` - Current user ID (test@test.com)

### Test Credentials
- `test_email` - Test user email (test@test.com)
- `test_password` - Test user password (test123)

### Dynamic Variables
- `document_id` - Document ID (set after upload)
- `quiz_id` - Quiz ID (set after generation)
- `task_id` - Task ID (set for tracking)
- `notification_id` - Notification ID (set after creation)

### Content Variables
- `search_query` - Search term for indexing
- `quiz_topic` - Topic for quiz generation
- `quiz_difficulty` - Quiz difficulty level
- `quiz_questions` - Number of questions
- `ollama_prompt` - Prompt for LLM testing

## 🧪 Testing Scenarios

### Scenario 1: New User Registration
1. Run "Register User" with new credentials
2. Run "Login User" with new credentials
3. Run "Get Current User" to verify profile

### Scenario 2: Document Upload and Processing
1. Run "Upload Document" with a PDF file
2. Copy the returned `document_id`
3. Run "Index Document" with the document ID
4. Run "Search Documents" to test search
5. Run "Get Document Chunks" to see processed content

### Scenario 3: Quiz Generation
1. Run "Generate Quiz" with topic and parameters
2. Copy the returned `quiz_id`
3. Run "Get Quiz" to see full quiz content
4. Run "List Quizzes" to see all user quizzes

### Scenario 4: Task Status Tracking
1. Run "Create Task Status" to start tracking
2. Run "Update Task Status" to update progress
3. Run "Get Task Status" to check current status
4. Run "Get User Task Statuses" to see all tasks

### Scenario 5: Notification Testing
1. Run "Create Notification" to send notification
2. Copy the returned `notification_id`
3. Run "Get User Notifications" to list notifications
4. Run "Mark Notification as Read" to update status

## 🔍 Troubleshooting

### Common Issues

1. **Authentication Failed:**
   - Ensure services are running: `docker-compose -f docker-compose.dev.yml ps`
   - Check if test data exists: `./scripts/seed_data_docker.sh`
   - Verify login credentials in environment variables

2. **Service Unavailable:**
   - Check service health: Run "Health Check" for each service
   - Verify ports are accessible: `curl http://localhost:8000/health`
   - Check Docker logs: `docker-compose -f docker-compose.dev.yml logs`

3. **File Upload Issues:**
   - Ensure MinIO is running: `docker ps | grep minio`
   - Check MinIO console: http://localhost:9001
   - Verify file format is supported (PDF, DOCX, XLSX, TXT)

4. **Quiz Generation Fails:**
   - Ensure Ollama is running: `docker ps | grep ollama`
   - Check Ollama API: `curl http://localhost:11434/api/tags`
   - Verify Llama2 model is downloaded

### Debug Commands

```bash
# Check all services
docker-compose -f docker-compose.dev.yml ps

# View service logs
docker-compose -f docker-compose.dev.yml logs [service-name]

# Test API Gateway
curl http://localhost:8000/health

# Test Ollama
curl -X POST http://localhost:11434/api/generate \
  -H 'Content-Type: application/json' \
  -d '{"model": "llama2", "prompt": "Hello"}'

# Test MinIO
curl http://localhost:9001
```

## 📊 Expected Responses

### Successful Authentication
```json
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "token_type": "bearer"
}
```

### Document Upload Success
```json
{
  "id": "uuid-here",
  "filename": "document.pdf",
  "content_type": "application/pdf",
  "status": "processing",
  "file_size": 1024000,
  "created_at": "2024-01-01T00:00:00Z"
}
```

### Quiz Generation Success
```json
{
  "id": "uuid-here",
  "title": "Machine Learning Quiz",
  "topic": "Machine Learning",
  "difficulty": "intermediate",
  "num_questions": 5,
  "created_at": "2024-01-01T00:00:00Z"
}
```

## 🎯 Best Practices

1. **Always start with Health Checks** to verify services are running
2. **Use the Login User endpoint first** to get authentication token
3. **Save returned IDs** to environment variables for subsequent requests
4. **Test error scenarios** by using invalid data
5. **Monitor task status** for long-running operations
6. **Use WebSocket connections** for real-time notifications

## 🔗 Related Documentation

- [Main README](../README.md) - Project overview and setup
- [API Documentation](../services/*/app/main.py) - Individual service docs
- [Development Setup](../scripts/setup-dev.sh) - Environment setup script

---

**Happy Testing! 🚀** 