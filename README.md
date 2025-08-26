# Study AI Platform

A comprehensive AI-powered study platform with document processing, quiz generation, and intelligent clarification flows.

## 🚀 **New: Extensible Clarification Backend**

The clarifier service now supports multiple flows with a slot-filling engine:

- **quiz_setup** (fully implemented) - Collects question types, difficulty, and count
- **doc_summary** (scaffold) - Future: summary length, audience, style
- **doc_highlights** (scaffold) - Future: bullet count, citations
- **doc_conclusion** (scaffold) - Future: thesis, length

## 🏗️ **Architecture**

### Core Services
- **API Gateway** (port 8000) - Main entry point and routing
- **Auth Service** (port 8001) - Authentication and user management
- **Document Service** (port 8002) - Document upload and management
- **Indexing Service** (port 8003) - Document indexing and search
- **Quiz Service** (port 8004) - Quiz generation and management
- **Notification Service** (port 8005) - Real-time notifications
- **Clarifier Service** (port 8010) - **NEW: Extensible clarification flows**
- **Question Budget Service** (port 8011) - Question count calculation

## 🔍 **Indexing Service - Document Processing & Vector Search**

The indexing service provides intelligent document chunking and vector-based search capabilities.

### ✂️ **Chunking Modes**

#### Dynamic Chunking (LaBSE-aware) ⭐ **ACTIVE**
- **Mode**: `CHUNK_MODE=DYNAMIC`
- **Base Tokens**: 320
- **Min/Max Tokens**: 180-480
- **Sentence Overlap Ratio**: 0.12
- **LaBSE Max Tokens**: 512
- **Density Weights**: Symbols (0.4), Average Words (0.3), Numbers (0.3)

#### Fixed Chunking (Legacy)
- **Mode**: `CHUNK_MODE=FIXED`
- **Chunk Size**: 1000 characters
- **Overlap**: 200 characters

### 🤖 **Vector Model**
- **Embedding Model**: `sentence-transformers/LaBSE`
- **Dimensions**: 384
- **Language Support**: Multi-language (LaBSE)

### 🔧 **API Endpoints**
- **Health**: `/health` - Service status
- **Configuration**: `/debug-config` - Current config values
- **Indexing**: `/index` - Document processing
- **Search**: `/search` - Vector similarity search
- **Category Search**: `/search/category` - Category-based search
- **Subject Search**: `/search/subject` - Subject-based search
- **Chunks**: `/chunks/{document_id}` - Retrieve chunks
- **Statistics**: `/stats/category/{id}`, `/stats/subject/{id}` - Usage stats

### ⚙️ **Environment Configuration**
All configuration is loaded from Docker Compose environment variables:
```yaml
environment:
  CHUNK_MODE: DYNAMIC
  CHUNK_BASE_TOKENS: 320
  CHUNK_MIN_TOKENS: 180
  CHUNK_MAX_TOKENS: 480
  EMBEDDING_MODEL: sentence-transformers/LaBSE
```

### 📊 **Current Status**
- ✅ **Service**: Fully operational
- ✅ **Configuration**: All environment variables loaded correctly
- ✅ **Chunking**: DYNAMIC mode active
- ✅ **API**: Clean, production-ready endpoints
- ✅ **Test Functions**: Removed for production use

### Background Workers
- **Document Worker** - Document processing
- **Indexing Worker** - Document indexing
- **Quiz Worker** - Quiz generation

### Infrastructure
- **PostgreSQL** - Primary databases
- **Redis** - Caching and message brokering
- **MinIO** - S3-compatible object storage
- **Ollama** - Local LLM inference

## 🔧 **Clarifier Service - New Features**

### Flow Engine Architecture

The clarifier service now uses a **slot-filling engine** that:

1. **Deterministic Parsing** - Parses user input without LLM calls
2. **LLM Extraction** - Optional feature-flagged JSON extraction
3. **Flow Validation** - Ensures data integrity across slots
4. **Extensible Design** - Easy to add new flows

### Supported Flows

#### 1. Quiz Setup Flow (Fully Implemented)
**Slots:**
- `question_types` - Multiple choice, true/false, fill-in-blank, short answer
- `difficulty` - Easy, medium, hard, mixed
- `requested_count` - Number of questions (5 to max from budget service)

**Example Flow:**
```bash
# Start quiz setup
curl -X POST http://localhost:8010/clarifier/start \
  -H "Content-Type: application/json" \
  -d '{
    "sessionId": "session-123",
    "userId": "user-456",
    "subjectId": "subject-789",
    "docIds": ["doc-1", "doc-2"],
    "flow": "quiz_setup"
  }'

# Response:
{
  "sessionId": "session-123",
  "flow": "quiz_setup",
  "nextPrompt": "What types of questions would you like? You can choose multiple: mcq, true_false, fill_blank, short_answer",
  "ui": {
    "quick": ["mcq", "true_false", "fill_blank", "short_answer"]
  }
}

# Fill question types
curl -X POST http://localhost:8010/clarifier/ingest \
  -H "Content-Type: application/json" \
  -d '{
    "sessionId": "session-123",
    "text": "mcq and true_false"
  }'

# Response:
{
  "stage": "next_slot",
  "filled": {
    "question_types": ["mcq", "true_false"]
  },
  "nextPrompt": "What difficulty level would you prefer? Choose from: easy, medium, hard, mixed",
  "ui": {
    "quick": ["easy", "medium", "hard", "mixed"]
  }
}

# Fill difficulty
curl -X POST http://localhost:8010/clarifier/ingest \
  -H "Content-Type: application/json" \
  -d '{
    "sessionId": "session-123",
    "text": "hard"
  }'

# Fill count
curl -X POST http://localhost:8010/clarifier/ingest \
  -H "Content-Type: application/json" \
  -d '{
    "sessionId": "session-123",
    "text": "15"
  }'

# Flow completes automatically and calls quiz service
```

#### 2. Document Summary Flow (Scaffold)
**Slots:**
- `summary_length` - Short, medium, long
- `audience` - K12, university, teacher
- `style` - Concise, detailed

#### 3. Document Highlights Flow (Scaffold)
**Slots:**
- `bullet_count` - Number of highlight points (3-10)
- `include_citations` - Boolean for citations

#### 4. Document Conclusion Flow (Scaffold)
**Slots:**
- `thesis` - Main thesis statement
- `length` - Short or medium

### Deterministic Parsers

The service includes intelligent parsers that understand:

**Question Types:**
- "mcq", "multiple choice", "choice" → `mcq`
- "true/false", "true false", "t/f", "tf" → `true_false`