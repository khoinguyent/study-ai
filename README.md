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
- "fill in the blank", "blank" → `fill_blank`
- "short answer", "essay" → `short_answer`

**Difficulty:**
- "easy", "simple", "basic" → `easy`
- "medium", "moderate" → `medium`
- "hard", "difficult", "advanced" → `hard`
- "mixed", "varied", "all" → `mixed`

**Counts:**
- "one", "two", "three" → 1, 2, 3
- "max", "maximum", "all" → maximum allowed
- Numeric patterns: "12 questions" → 12

### LLM Extractor (Feature Flagged)

When `USE_LLM_EXTRACTOR=true`, the service can handle complex inputs:

```bash
# Single input fills multiple slots
curl -X POST http://localhost:8010/clarifier/ingest \
  -H "Content-Type: application/json" \
  -d '{
    "sessionId": "session-123",
    "text": "12 hard MCQs and some true/false"
  }'

# LLM extracts: question_types=["mcq", "true_false"], difficulty="hard", requested_count=12
```

### Environment Variables

```bash
# Clarifier Service
PORT=8010
BUDGET_URL=http://question-budget-svc:8011
QUIZ_URL=http://quiz-service:8004
USE_LLM_EXTRACTOR=false  # Feature flag for LLM extraction
EXTRACTOR_URL=           # Optional LLM service URL
NODE_ENV=development
LOG_LEVEL=info
```

## 🚀 **Quick Start**

### 1. Start All Services
```bash
docker-compose up --build
```

### 2. Test the Clarifier Service
```bash
# Health check
curl http://localhost:8010/health

# Start quiz setup flow
curl -X POST http://localhost:8010/clarifier/start \
  -H "Content-Type: application/json" \
  -d '{
    "sessionId": "test-1",
    "userId": "user-1",
    "subjectId": "subject-1",
    "docIds": ["doc-1"],
    "flow": "quiz_setup"
  }'
```

### 3. Run Tests
```bash
cd services/clarifier-svc
npm install
npm test
npm run test:coverage
```

## 🔍 **API Endpoints**

### Clarifier Service

| Endpoint | Method | Description |
|-----------|--------|-------------|
| `/health` | GET | Service health check |
| `/clarifier/start` | POST | Start a new clarification flow |
| `/clarifier/ingest` | POST | Process user input for current slot |
| `/clarifier/confirm` | POST | **Legacy**: Confirm study session (backwards compatible) |

### Request/Response Examples

#### Start Flow
```typescript
// Request
{
  sessionId: string;
  userId: string;
  subjectId: string;
  docIds: string[];
  flow?: 'quiz_setup' | 'doc_summary' | 'doc_highlights' | 'doc_conclusion';
}

// Response
{
  sessionId: string;
  flow: string;
  nextPrompt: string;
  ui: { quick?: string[] };
}
```

#### Ingest Input
```typescript
// Request
{
  sessionId: string;
  text: string;
}

// Response
{
  stage: 'next_slot' | 'complete' | 'redirect' | 'clarification' | 'error';
  filled: Record<string, any>;
  nextPrompt?: string;
  ui?: { quick?: string[] };
  done?: boolean;
}
```

## 🧪 **Testing**

### Parser Tests
```bash
npm run test parsers.test.ts
```

### Flow Runner Tests
```bash
npm run test runner.test.ts
```

### Coverage Report
```bash
npm run test:coverage
```

## 🔧 **Development**

### Adding New Flows

1. **Create Flow File** (`src/flows/new_flow.ts`)
2. **Define Slots** with types, prompts, and validation
3. **Register Flow** in `src/routes/clarifier.ts`
4. **Add Tests** in `__tests__/`

### Flow Structure
```typescript
export const newFlow: FlowSpec = {
  id: 'new_flow',
  
  async init(ctx: any) {
    // Initialize dynamic context
    return { /* context data */ };
  },

  slots: [
    {
      key: 'slot_name',
      type: 'enum' | 'multi_enum' | 'int' | 'bool' | 'string',
      prompt: (ctx: any) => `User prompt text`,
      ui: (ctx: any) => ({ quick: ['option1', 'option2'] }),
      allowed: ['option1', 'option2'],
      min?: number,
      max?: number,
      required?: boolean,
      parserHint?: 'difficulty' | 'qtype' | 'count' | 'length' | 'audience' | 'style'
    }
  ],

  async validate(filled: Record<string, any>, ctx: any) {
    // Validate filled slots
    return { ok: boolean, errors?: string[], filled: any };
  },

  async finalize(filled: Record<string, any>, ctx: any) {
    // Execute flow logic
    return { status: number, body: any };
  }
};
```

## 🎯 **Key Features**

✅ **Extensible Flow Engine** - Easy to add new clarification flows  
✅ **Deterministic Parsing** - No LLM calls for basic parsing  
✅ **LLM Extraction** - Feature-flagged for complex inputs  
✅ **Slot Validation** - Ensures data integrity  
✅ **Backwards Compatibility** - Existing `/confirm` endpoint still works  
✅ **Comprehensive Testing** - Jest tests with coverage  
✅ **Type Safety** - Full TypeScript implementation  
✅ **Production Ready** - Error handling, logging, health checks  

## 🚀 **Next Steps**

1. **Implement Future Flows** - Complete doc_summary, doc_highlights, doc_conclusion
2. **Add More Parsers** - Support for additional input formats
3. **Persistent Storage** - Move session state to Redis/database
4. **Advanced UI** - Rich interface for flow management
5. **Flow Templates** - Pre-configured flow configurations

---

The Study AI Platform now has a **production-ready, extensible clarification backend** that can handle complex user interactions while maintaining clean, maintainable code! 🎉 