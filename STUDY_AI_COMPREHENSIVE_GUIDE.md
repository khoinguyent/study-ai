# Study AI Platform - Comprehensive Guide

A comprehensive AI-powered study platform with document processing, quiz generation, and intelligent clarification flows.

## Table of Contents

1. [Platform Overview](#platform-overview)
2. [Architecture](#architecture)
3. [Quiz Generation System](#quiz-generation-system)
4. [Quiz Toast System](#quiz-toast-system)
5. [Document Processing](#document-processing)
6. [Clarifier Service](#clarifier-service)
7. [Infrastructure & Deployment](#infrastructure--deployment)
8. [Development Workflow](#development-workflow)
9. [Troubleshooting](#troubleshooting)
10. [API Reference](#api-reference)

---

## Platform Overview

### 🚀 **New: Extensible Clarification Backend**

The clarifier service now supports multiple flows with a slot-filling engine:

- **quiz_setup** (fully implemented) - Collects question types, difficulty, and count
- **doc_summary** (scaffold) - Future: summary length, audience, style
- **doc_highlights** (scaffold) - Future: bullet count, citations
- **doc_conclusion** (scaffold) - Future: thesis, length

### Core Features

- **Document Upload & Processing**: Intelligent chunking and indexing
- **AI-Powered Quiz Generation**: Multiple question types with real-time generation
- **Real-time Notifications**: SSE-based progress tracking and completion alerts
- **Multi-language Support**: LaBSE-based vector search and embedding
- **Extensible Clarification Flows**: Slot-filling engine for user input collection

---

## Architecture

### Core Services

- **API Gateway** (port 8000) - Main entry point and routing
- **Auth Service** (port 8001) - Authentication and user management
- **Document Service** (port 8002) - Document upload and management
- **Indexing Service** (port 8003) - Document indexing and search
- **Quiz Service** (port 8004) - Quiz generation and management
- **Notification Service** (port 8005) - Real-time notifications
- **Clarifier Service** (port 8010) - **NEW: Extensible clarification flows**
- **Question Budget Service** (port 8011) - Question count calculation

### Background Workers
- **Document Worker** - Document processing
- **Indexing Worker** - Document indexing
- **Quiz Worker** - Quiz generation

### Infrastructure
- **PostgreSQL** - Primary databases
- **Redis** - Caching and message brokering
- **MinIO** - S3-compatible object storage
- **Ollama** - Local LLM inference

---

## Quiz Generation System

### 🎯 **Goal Achieved**

After the dashboard triggers quiz generation (OpenAI), we now:
- ✅ Store the LLM JSON in quizzes (already works)
- ✅ Immediately create a quiz session from that quiz_id
- ✅ Stream job progress via SSE
- ✅ Show a toast with "Open quiz" that links to `/quiz/session/:sessionId`

### **Implementation Summary**

#### **1. Quiz Service - Session Creation Endpoint**

**New Endpoint**: `POST /quiz-sessions/from-quiz/{quiz_id}`

- **Location**: `services/quiz-service/app/main.py`
- **Functionality**: Creates a new quiz session from an existing quiz
- **Features**:
  - Question shuffling (optional)
  - Automatic session question creation
  - Proper data mapping from quiz to session format
- **Response**: `{"session_id": "...", "count": N}`

#### **2. API Gateway - Enhanced Quiz Generation**

**Updated Endpoint**: `POST /api/quizzes/generate`

- **Location**: `services/api-gateway/app/main.py`
- **Enhancement**: Automatically creates session after quiz generation
- **Flow**:
  1. Generate quiz via quiz service
  2. Extract quiz_id from response
  3. Create session via new endpoint
  4. Return enhanced response with session_id

#### **3. Frontend - Updated API and Hooks**

**Updated Files**:
- `web/src/api/quiz.ts` - Enhanced startQuizJob to handle session_id
- `web/src/hooks/useQuizJobToasts.ts` - Updated SSE event handling
- `web/src/components/StartStudyLauncher.tsx` - Direct navigation if session available

**Key Features**:
- Direct navigation to quiz session if immediately available
- Fallback to SSE progress monitoring if session creation is delayed
- Proper error handling and user feedback

#### **4. SSE Event Contract**

**Standardized Event Format**:
```json
// Running
event: running
data: {"v":1,"jobId":"...","quizId":"..."}

// Progress
event: progress
data: {"v":1,"jobId":"...","progress":42,"stage":"generating"}

// Completed
event: completed
data: {"v":1,"jobId":"...","quizId":"...","sessionId":"..."}
```

### **User Experience Flow**

#### **Scenario 1: Immediate Session Creation**
1. User clicks "Generate Quiz" in dashboard
2. Quiz generation completes quickly
3. Session is created automatically
4. User is redirected directly to `/quiz/session/:sessionId`
5. Quiz loads immediately

#### **Scenario 2: Delayed Session Creation**
1. User clicks "Generate Quiz" in dashboard
2. Quiz generation starts
3. Progress toast shows "Generating quiz..."
4. SSE events stream progress updates
5. When complete, toast shows "Quiz ready" with "Open quiz" button
6. Clicking "Open quiz" navigates to `/quiz/session/:sessionId`

---

## Quiz Toast System

### Issues Identified and Fixed

#### 1. Duplicate Toasts Issue
**Problem**: Multiple "Generating quiz..." toasts were being shown simultaneously.

**Root Cause**: 
- `useQuizGenerationToasts` hook was showing an initial toast when `jobId` was set
- `useJobProgress` hook was also calling `onQueued` which showed another toast with the same ID
- This resulted in duplicate toasts with the same `quizjob:${jobId}` ID

**Fix**: 
- Removed the automatic initial toast from `useQuizGenerationToasts` hook
- Let `useJobProgress` handle the `onQueued` callback exclusively
- This ensures only one toast is shown when quiz generation starts

#### 2. SSE MIME Type Error
**Problem**: SSE connection was failing with error: "EventSource's response has a MIME type ("application/json") that is not "text/event-stream""

**Root Cause**: 
- Notification service was returning `application/json` instead of `text/event-stream` for SSE endpoints
- The SSE endpoint was not properly proxying to the quiz service

**Fix**: 
- Updated notification service SSE endpoint to properly proxy to quiz service
- Ensured correct MIME type (`text/event-stream`) is returned
- Added proper error handling for SSE streaming

#### 3. Missing Quiz Completion Event
**Problem**: Quiz completion events were not being published, so the "Quiz ready" toast was not showing.

**Root Cause**: 
- Quiz generation endpoint was not publishing `quiz_generated` events
- Notification service was not handling quiz events properly

**Fix**: 
- Added quiz event publishing to quiz generation endpoint
- Added quiz event handler to notification service
- Registered quiz event handlers in the event consumer

### Expected Behavior After Fixes

1. **Single Initial Toast**: When quiz generation starts, only one "Generating quiz..." toast should appear
2. **SSE Connection**: SSE connection should establish successfully without MIME type errors
3. **Progress Updates**: Toast should update with progress as quiz generation proceeds
4. **Completion Toast**: When quiz generation completes, the progress toast should be replaced with a "Quiz ready" toast with an "Open" action button

---

## Document Processing

### 🔍 **Indexing Service - Document Processing & Vector Search**

The indexing service provides intelligent document chunking and vector-based search capabilities.

#### ✂️ **Chunking Modes**

##### Dynamic Chunking (LaBSE-aware) ⭐ **ACTIVE**
- **Mode**: `CHUNK_MODE=DYNAMIC`
- **Base Tokens**: 320
- **Min/Max Tokens**: 180-480
- **Sentence Overlap Ratio**: 0.12
- **LaBSE Max Tokens**: 512
- **Density Weights**: Symbols (0.4), Average Words (0.3), Numbers (0.3)

##### Fixed Chunking (Legacy)
- **Mode**: `CHUNK_MODE=FIXED`
- **Chunk Size**: 1000 characters
- **Overlap**: 200 characters

#### 🤖 **Vector Model**
- **Embedding Model**: `sentence-transformers/LaBSE`
- **Dimensions**: 384
- **Language Support**: Multi-language (LaBSE)

#### 🔧 **API Endpoints**
- **Health**: `/health` - Service status
- **Configuration**: `/debug-config` - Current config values
- **Indexing**: `/index` - Document processing
- **Search**: `/search` - Vector similarity search
- **Category Search**: `/search/category` - Category-based search
- **Subject Search**: `/search/subject` - Subject-based search
- **Chunks**: `/chunks/{document_id}` - Retrieve chunks
- **Statistics**: `/stats/category/{id}`, `/stats/subject/{id}` - Usage stats

#### ⚙️ **Environment Configuration**
All configuration is loaded from Docker Compose environment variables:
```yaml
environment:
  CHUNK_MODE: DYNAMIC
  CHUNK_BASE_TOKENS: 320
  CHUNK_MIN_TOKENS: 180
  CHUNK_MAX_TOKENS: 480
  EMBEDDING_MODEL: sentence-transformers/LaBSE
```

#### 📊 **Current Status**
- ✅ **Service**: Fully operational
- ✅ **Configuration**: All environment variables loaded correctly
- ✅ **Chunking**: DYNAMIC mode active
- ✅ **API**: Clean, production-ready endpoints
- ✅ **Test Functions**: Removed for production use

---

## Clarifier Service

### 🔧 **Clarifier Service - New Features**

#### Flow Engine Architecture

The clarifier service now uses a **slot-filling engine** that:

1. **Deterministic Parsing** - Parses user input without LLM calls
2. **LLM Extraction** - Optional feature-flagged JSON extraction
3. **Flow Validation** - Ensures data integrity across slots
4. **Extensible Design** - Easy to add new flows

#### Supported Flows

##### **quiz_setup** (Fully Implemented)
- **Purpose**: Collect quiz generation parameters
- **Slots**:
  - `question_types`: Array of question types (MCQ, True/False, etc.)
  - `difficulty`: Easy, Medium, Hard, Mixed
  - `question_count`: Number of questions (5-50)
  - `question_mix`: Optional percentage distribution
- **Validation**: Ensures valid question types and count ranges

##### **doc_summary** (Scaffold)
- **Purpose**: Generate document summaries
- **Slots**: Summary length, audience, style (future implementation)

##### **doc_highlights** (Scaffold)
- **Purpose**: Extract key highlights from documents
- **Slots**: Bullet count, citations (future implementation)

##### **doc_conclusion** (Scaffold)
- **Purpose**: Generate document conclusions
- **Slots**: Thesis, length (future implementation)

#### API Endpoints

- **Start Flow**: `POST /flows/{flow_id}/start`
- **Ingest Input**: `POST /flows/{flow_id}/ingest`
- **Get Status**: `GET /flows/{flow_id}/status`
- **Complete Flow**: `POST /flows/{flow_id}/complete`

---

## Question Data Structure

### Updated Question Types with "type" Field

The question data structure has been updated to include a standardized "type" field across all question types:

#### **Question Type Definitions**

```typescript
export type QuestionType = 
  | "single_choice"    // Multiple choice with one correct answer
  | "multiple_choice"  // Multiple choice with multiple correct answers
  | "true_false"       // True/False questions
  | "fill_blank"       // Fill in the blank questions
  | "short_answer";    // Short answer questions
```

#### **Question Data Structure**

```typescript
// Base question interface
export interface QuestionBase {
  id: string;
  type: QuestionType;           // REQUIRED: Standardized type field
  prompt: string;               // The question text
  points?: number;              // Points for this question
  explanation?: string;         // Explanation revealed after submit
}

// Single Choice Question
export interface SingleChoiceQuestion extends QuestionBase {
  type: "single_choice";
  options: QuestionOption[];
  correctChoiceId?: string;     // Revealed after submit
}

// Multiple Choice Question
export interface MultipleChoiceQuestion extends QuestionBase {
  type: "multiple_choice";
  options: QuestionOption[];
  correctChoiceIds?: string[];   // Revealed after submit
}

// True/False Question
export interface TrueFalseQuestion extends QuestionBase {
  type: "true_false";
  trueLabel?: string;           // Custom label for true option
  falseLabel?: string;          // Custom label for false option
  correct?: boolean;            // Revealed after submit
}

// Fill in the Blank Question
export interface FillBlankQuestion extends QuestionBase {
  type: "fill_blank";
  blanks: number;                // Number of blanks in prompt
  labels?: string[];             // Optional labels per blank
  correctValues?: string[];      // Revealed after submit
}

// Short Answer Question
export interface ShortAnswerQuestion extends QuestionBase {
  type: "short_answer";
  minWords?: number;             // Minimum word count
  rubric?: string;              // Grading rubric
}

// Question Option
export interface QuestionOption {
  id: string;
  text: string;                  // Option text
  isCorrect?: boolean;           // Whether this option is correct
}

// Union type for all question types
export type Question = 
  | SingleChoiceQuestion
  | MultipleChoiceQuestion
  | TrueFalseQuestion
  | FillBlankQuestion
  | ShortAnswerQuestion;
```

#### **Answer Data Structure**

```typescript
export type Answer = 
  | { kind: "single"; choiceId: string | null }
  | { kind: "multiple"; choiceIds: string[] }
  | { kind: "boolean"; value: boolean | null }
  | { kind: "blanks"; values: string[] }
  | { kind: "text"; value: string };

export type AnswerMap = {
  [questionId: string]: Answer;
};
```

#### **Quiz Session Structure**

```typescript
export interface QuizSession {
  id: string;
  quizId: string;
  userId: string;
  questions: Question[];
  answers: AnswerMap;
  score?: number;
  completed: boolean;
  createdAt: string;
  updatedAt: string;
}
```

#### **API Response Format**

```json
{
  "session_id": "session-123",
  "quiz_id": "quiz-456",
  "questions": [
    {
      "id": "q1",
      "type": "single_choice",
      "prompt": "What is the capital of France?",
      "options": [
        {"id": "a", "text": "London", "isCorrect": false},
        {"id": "b", "text": "Paris", "isCorrect": true},
        {"id": "c", "text": "Berlin", "isCorrect": false}
      ],
      "points": 1
    },
    {
      "id": "q2",
      "type": "true_false",
      "prompt": "The Earth is flat.",
      "correct": false,
      "points": 1
    },
    {
      "id": "q3",
      "type": "fill_blank",
      "prompt": "The capital of Japan is _____.",
      "blanks": 1,
      "correctValues": ["Tokyo"],
      "points": 1
    }
  ]
}
```

---

## Infrastructure & Deployment

### Multi-Environment Workflow

#### **Environment Types**
1. **Local Development** - Docker Compose with local services
2. **Cloud Development** - AWS-based development environment
3. **Production** - Fully managed AWS infrastructure

#### **Deployment Options**

##### **Local Development**
```bash
# Start all services locally
docker-compose up -d

# Build and start with custom config
./build-and-start.sh
```

##### **Cloud Deployment**
```bash
# Deploy to AWS
./deploy-cloud.sh

# Setup CI/CD pipeline
./scripts/setup-ci-cd.sh
```

### Infrastructure Architecture

#### **AWS Services Used**
- **EC2** - Application servers
- **RDS** - PostgreSQL databases
- **ElastiCache** - Redis caching
- **S3** - Document storage
- **SageMaker** - AI model hosting
- **CloudFront** - CDN for static assets
- **Route 53** - DNS management

#### **Security**
- **IAM** - Role-based access control
- **VPC** - Network isolation
- **Security Groups** - Firewall rules
- **KMS** - Key management
- **WAF** - Web application firewall

---

## Development Workflow

### Quick Reference

#### **Starting Development**
```bash
# Clone and setup
git clone <repository>
cd study-ai
./scripts/setup-dev.sh

# Start services
docker-compose up -d

# Check status
docker-compose ps
```

#### **Testing**
```bash
# Run all tests
./test-quiz-generation.sh

# Test specific components
python test_quiz_generation_flow.py
python test_session_creation.py
```

#### **Database Management**
```bash
# Clear all databases
./scripts/clear_all_databases.sh

# Seed test data
./scripts/seed_data_docker.sh
```

### Route Ordering Fix

#### **Problem**
API Gateway routes were conflicting due to parameter matching order.

#### **Solution**
1. **Early Route Placement**: Move specific routes before generic ones
2. **Parameter Validation**: Add proper parameter validation
3. **Route Priority**: Use explicit route ordering

#### **Implementation**
```python
# Early route placement for specific endpoints
@app.get("/api/test-quiz-route/{session_id}")
async def gateway_view_quiz_session_early(session_id: str, request: Request):
    # Specific route implementation

# Generic routes placed after specific ones
@app.get("/api/{path:path}")
async def generic_proxy(path: str, request: Request):
    # Generic proxy implementation
```

---

## Troubleshooting

### Common Issues

#### **Docker Worker Issues**
- **Problem**: Workers not processing tasks
- **Solution**: Check Redis connection and task queue status
- **Debug**: Use `./troubleshoot-docker.sh`

#### **Quiz Generation Failures**
- **Problem**: Quiz generation hanging or failing
- **Solution**: Check AI provider configuration and API keys
- **Debug**: Monitor logs with `./monitor_quiz.sh`

#### **SSE Connection Issues**
- **Problem**: Real-time updates not working
- **Solution**: Verify MIME type and proxy configuration
- **Debug**: Check browser console for EventSource errors

### Debugging Tools

#### **Log Monitoring**
```bash
# Monitor all services
docker-compose logs -f

# Monitor specific service
docker-compose logs -f quiz-service

# Monitor with timestamps
docker-compose logs -f --timestamps
```

#### **Database Inspection**
```bash
# Connect to database
docker-compose exec quiz-db psql -U postgres -d quizdb

# Check quiz sessions
SELECT * FROM quiz_sessions ORDER BY created_at DESC LIMIT 10;
```

#### **Redis Inspection**
```bash
# Connect to Redis
docker-compose exec redis redis-cli

# Check task queues
KEYS *celery*
```

---

## API Reference

### Core Endpoints

#### **Quiz Generation**
```http
POST /api/quizzes/generate
Content-Type: application/json

{
  "docIds": ["doc1", "doc2"],
  "numQuestions": 10,
  "questionTypes": ["MCQ", "True/False"],
  "difficulty": "medium",
  "language": "auto"
}
```

#### **Quiz Sessions**
```http
GET /api/quiz-sessions/{session_id}
POST /api/quiz-sessions/{session_id}/answers
POST /api/quiz-sessions/{session_id}/submit
```

#### **Document Management**
```http
POST /api/documents/upload
GET /api/documents
GET /api/documents/{id}/download
```

#### **Real-time Events**
```http
GET /api/study-sessions/events?job_id={job_id}
GET /api/uploads/events?userId={userId}
```

### Authentication

All API endpoints require authentication via JWT tokens:

```http
Authorization: Bearer <jwt_token>
```

### Error Handling

Standard error response format:

```json
{
  "error": "Error message",
  "status_code": 400,
  "details": "Additional error details"
}
```

---

## Files Modified

### **Backend**
- `services/quiz-service/app/main.py` - Added session creation endpoint, updated SSE events
- `services/api-gateway/app/main.py` - Enhanced quiz generation with automatic session creation
- `services/notification-service/app/main.py` - Fixed SSE endpoint and added quiz event handlers

### **Frontend**
- `web/src/api/quiz.ts` - Enhanced startQuizJob response handling
- `web/src/hooks/useQuizJobToasts.ts` - Updated SSE event handling and navigation
- `web/src/components/StartStudyLauncher.tsx` - Added direct navigation logic
- `web/src/components/quiz/useQuizToasts.ts` - Fixed duplicate toast issue

### **Testing**
- `test_session_creation.py` - Tests the new session creation endpoint
- `test_quiz_generation_flow.py` - Tests the complete flow through API gateway

---

## Conclusion

The Study AI Platform now provides a comprehensive, production-ready solution for AI-powered quiz generation with:

- ✅ **Real-time Progress Tracking**: SSE-based progress updates
- ✅ **Immediate Session Creation**: Automatic quiz session creation
- ✅ **Extensible Clarification Flows**: Slot-filling engine for user input
- ✅ **Multi-language Document Processing**: LaBSE-based vector search
- ✅ **Robust Error Handling**: Comprehensive error management
- ✅ **Scalable Architecture**: Microservices with event-driven communication

The platform is ready for production deployment and can handle complex quiz generation workflows with real-time user feedback.
