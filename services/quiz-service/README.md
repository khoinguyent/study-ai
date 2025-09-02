# Quiz Service - AI-Powered Quiz Generation

## Overview

The Quiz Service is a microservice that generates AI-powered quizzes using multiple LLM providers (OpenAI, Ollama, Hugging Face). It implements direct document chunk processing and supports multiple question types with comprehensive validation and grading.

## Features

- 🚀 **Multi-LLM Support**: OpenAI, Ollama, and Hugging Face
- 📚 **Direct Chunks Generation**: Uses document chunks directly from database
- 🌍 **Language Auto-Detection**: Automatically detects and enforces output language
- ✅ **Multiple Question Types**: MCQ, True/False, Fill-in-Blank, Short Answer
- 🔄 **Validation Pipeline**: JSON structure, citations, and type validation
- 📊 **Session Management**: Quiz sessions with deterministic shuffling
- 🎯 **Grading System**: Question-type specific grading with text normalization
- 🐳 **Docker Ready**: Fully containerized with all dependencies

## Quick Start

### Using Docker (Recommended)

```bash
# Build and run with docker-compose
docker-compose up -d quiz-service

# Or build individually
docker build -t quiz-service .
docker run -p 8004:8004 quiz-service
```

### Local Development

```bash
# Install dependencies
pip install -r requirements.txt

# Run the service
uvicorn app.main:app --host 0.0.0.0 --port 8004
```

## API Endpoints

### Health Check
```
GET /health
```

### Test Endpoints
```
GET /test-openai    # Test OpenAI connectivity
GET /test-ollama    # Test Ollama connectivity
```

### Quiz Generation
```
POST /quizzes/generate
POST /study-sessions/start
```

### Quiz Session Management
```
POST /quizzes/{quiz_id}/sessions          # Create new session
GET /quizzes/sessions/{session_id}/view   # Safe view (no answers)
POST /quizzes/sessions/{session_id}/answers # Save answers
POST /quizzes/sessions/{session_id}/submit # Submit and grade
```

## Configuration

### Environment Variables

```bash
# Database
DATABASE_URL=postgresql://user:pass@localhost/quizdb

# LLM Providers
OPENAI_API_KEY=your_openai_key
OPENAI_MODEL=gpt-3.5-turbo
OPENAI_TEMPERATURE=0.7
OPENAI_MAX_TOKENS=2000
OPENAI_BASE_URL=https://api.openai.com/v1

OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llama2:7b

HUGGINGFACE_TOKEN=your_hf_token
QUESTION_GENERATION_MODEL=google/flan-t5-base

# Service Settings
QUIZ_GENERATION_STRATEGY=openai  # auto, openai, ollama, huggingface
QUIZ_LANG_MODE=auto
QUIZ_LANG_DEFAULT=en
```

## Quiz JSON Structure

The service generates quizzes in a standardized JSON format that supports all question types. Here's the complete structure:

### Main Quiz Structure

```json
{
  "title": "string",
  "description": "string",
  "questions": [
    // Question objects (see below)
  ],
  "output_language": "en",
  "source_type": "document",
  "source_id": "string"
}
```

### Question Types

#### 1. Multiple Choice (MCQ)

```json
{
  "stem": "What is the main cause of the historical event?",
  "options": [
    "Economic factors",
    "Political instability", 
    "Social changes",
    "Environmental factors"
  ],
  "correct_option": 1,
  "metadata": {
    "language": "en",
    "sources": [
      {
        "context_id": "chunk_1",
        "quote": "Political instability was the primary driver..."
      }
    ]
  }
}
```

#### 2. True/False

```json
{
  "stem": "The historical event had significant long-term effects.",
  "options": [
    "True",
    "False"
  ],
  "correct_option": 0,
  "metadata": {
    "language": "en",
    "sources": [
      {
        "context_id": "chunk_2",
        "quote": "The impact continues to be felt today..."
      }
    ]
  }
}
```

#### 3. Fill-in-Blank

```json
{
  "stem": "The key figure in the historical event was _____.",
  "blanks": 1,
  "correct_answer": "the leader",
  "metadata": {
    "language": "en",
    "sources": [
      {
        "context_id": "chunk_3",
        "quote": "This person played a crucial role..."
      }
    ]
  }
}
```

#### 4. Short Answer

```json
{
  "stem": "Explain the main causes of the historical event.",
  "rubric": {
    "key_points": [
      {
        "point": "Political instability",
        "weight": 0.4,
        "aliases": ["political unrest", "government instability"]
      },
      {
        "point": "Economic factors", 
        "weight": 0.3,
        "aliases": ["economic crisis", "financial problems"]
      },
      {
        "point": "Social changes",
        "weight": 0.3,
        "aliases": ["social unrest", "societal changes"]
      }
    ],
    "threshold": 0.7
  },
  "metadata": {
    "language": "en",
    "sources": [
      {
        "context_id": "chunk_4",
        "quote": "Multiple factors contributed to the event..."
      }
    ]
  }
}
```

## Architecture

### Core Components

1. **QuizGenerator Service** (`app/services/quiz_generator.py`)
   - Main service class with multiple generation strategies
   - Integrates with LLM providers
   - Handles prompt building and response processing

2. **LLM Providers** (`app/llm/providers/`)
   - `openai_adapter.py` - OpenAI integration
   - `ollama_adapter.py` - Ollama integration
   - `hf_adapter.py` - HuggingFace integration

3. **Session Management** (`app/services/`)
   - `session_service.py` - Quiz session creation and management
   - `grading_service.py` - Answer evaluation and scoring
   - `eval_utils.py` - Text normalization and pattern matching

4. **Language Detection** (`app/lang/`)
   - `detect.py` - Multi-library language detection
   - `language.py` - Language utilities

### Data Flow

```
Document Chunks → QuizGenerator → LLM Provider → Response Processing → Quiz JSON
                ↓
            Session Creation → User Interaction → Grading → Results
```

## Usage Examples

### Generate Quiz

```bash
curl -X POST http://localhost:8004/quizzes/generate \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer your-token" \
  -d '{
    "docIds": ["doc-123"],
    "numQuestions": 10,
    "difficulty": "medium",
    "questionTypes": ["mcq", "true_false", "fill_in_blank", "short_answer"]
  }'
```

### Create Quiz Session

```bash
curl -X POST http://localhost:8004/quizzes/{quiz_id}/sessions \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer your-token"
```

### Submit Answers

```bash
curl -X POST http://localhost:8004/quizzes/sessions/{session_id}/submit \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer your-token" \
  -d '{
    "answers": [
      {
        "session_question_id": "q1",
        "payload": "selected_option_id"
      }
    ]
  }'
```

## Development

### Project Structure

```
services/quiz-service/
├── app/
│   ├── main.py                 # FastAPI application
│   ├── services/
│   │   ├── quiz_generator.py   # Main quiz generation logic
│   │   ├── session_service.py  # Session management
│   │   └── grading_service.py  # Answer evaluation
│   ├── llm/providers/          # LLM integrations
│   ├── lang/                   # Language detection
│   └── prompts/                # Prompt templates
├── shared/                     # Shared utilities
├── requirements.txt            # Python dependencies
├── Dockerfile                  # Container configuration
└── README.md                   # This file
```

### Adding New Question Types

1. Update the prompt templates in `app/prompts/`
2. Add question type handling in `session_service.py`
3. Implement grading logic in `grading_service.py`
4. Update the JSON schema documentation

### Testing

```bash
# Test OpenAI integration
curl http://localhost:8004/test-openai

# Test quiz generation
curl -X POST http://localhost:8004/quizzes/generate \
  -H "Content-Type: application/json" \
  -d '{"docIds": ["test"], "numQuestions": 5}'
```

## Troubleshooting

### Common Issues

1. **OpenAI API Errors**: Check API key and model configuration
2. **Language Detection**: Verify `QUIZ_LANG_MODE` and `QUIZ_LANG_DEFAULT`
3. **Provider Initialization**: Check environment variables and provider availability

### Logs

```bash
# View service logs
docker-compose logs quiz-service

# Follow logs in real-time
docker-compose logs -f quiz-service
```

## Contributing

1. Follow the existing code structure
2. Add comprehensive tests for new features
3. Update documentation for any API changes
4. Ensure all question types are properly supported
