# Quiz Service

The Quiz Service is a core component of the Study AI platform that handles AI-powered quiz generation for educational content.

## Features

- **Multiple AI Backends**: Support for OpenAI, HuggingFace, and Ollama
- **Context-Aware Generation**: Creates quizzes based on specific documents, subjects, and categories
- **Real-time Progress Tracking**: WebSocket-based progress updates during quiz generation
- **Background Processing**: Celery-based asynchronous quiz generation
- **AI Clarifier**: Intelligent assistance for quiz setup and customization

## AI Models Supported

### 1. OpenAI (Recommended)
- **Models**: GPT-3.5-turbo, GPT-4, and other OpenAI models
- **Features**: High-quality quiz generation with JSON format enforcement
- **Configuration**: Set `QUIZ_GENERATION_STRATEGY=openai`

### 2. HuggingFace
- **Models**: Google Flan-T5 and other HuggingFace models
- **Features**: Open-source models with good performance
- **Configuration**: Set `QUIZ_GENERATION_STRATEGY=huggingface`

### 3. Ollama (Local)
- **Models**: Llama2:7b and other local models
- **Features**: Privacy-focused, runs locally
- **Configuration**: Set `QUIZ_GENERATION_STRATEGY=ollama`

### 4. Auto Strategy
- **Behavior**: Tries OpenAI first, then HuggingFace, falls back to Ollama
- **Configuration**: Set `QUIZ_GENERATION_STRATEGY=auto`

## Configuration

### Environment Variables

Create a `.env` file based on `env.example`:

```bash
# Quiz Generation Strategy
QUIZ_GENERATION_STRATEGY=openai

# OpenAI Configuration
OPENAI_API_KEY=your-openai-api-key-here
OPENAI_BASE_URL=https://api.openai.com/v1
OPENAI_MODEL=gpt-3.5-turbo
OPENAI_MAX_TOKENS=2000
OPENAI_TEMPERATURE=0.7

# HuggingFace Configuration
HUGGINGFACE_TOKEN=your-huggingface-token-here
HUGGINGFACE_API_URL=https://api-inference.huggingface.co/models
QUESTION_GENERATION_MODEL=google/flan-t5-base

# Ollama Configuration
OLLAMA_BASE_URL=http://ollama:11434
OLLAMA_MODEL=llama2:7b
```

## API Endpoints

### Health & Testing
- `GET /health` - Service health check
- `GET /test-openai` - Test OpenAI connectivity
- `GET /test-ollama` - Test Ollama connectivity

### Study Sessions
- `POST /study-sessions/start` - Start a new study session
- `GET /study-sessions/status` - Get session status
- `GET /study-sessions/events` - Get real-time events
- `POST /study-sessions/ingest` - Add input to session
- `POST /study-sessions/confirm` - Confirm and generate quiz

### Quiz Management
- `POST /quizzes/generate` - Generate a new quiz
- `POST /quizzes/generate-simple` - Generate quiz without auth (testing)
- `GET /quizzes/{quiz_id}` - Get specific quiz
- `GET /quizzes` - List user quizzes

### AI Clarifier
- `POST /clarifier/start` - Start AI clarifier session
- `POST /clarifier/ingest` - Process clarifier input

## Quiz Generation Process

1. **Session Start**: User initiates study session with parameters
2. **AI Processing**: Selected AI model generates questions based on context
3. **Progress Tracking**: Real-time updates via WebSocket events
4. **Quiz Delivery**: Final quiz with questions, options, and explanations

## Question Types Supported

- **Multiple Choice**: 4 options with correct answer and explanation
- **True/False**: Binary questions with explanations
- **Fill in the Blank**: Text completion questions

## Development

### Running Locally

```bash
cd services/quiz-service
pip install -r requirements.txt
uvicorn app.main:app --reload --host 0.0.0.0 --port 8004
```

### Docker

```bash
docker-compose up quiz-service
```

### Testing OpenAI Integration

1. Set your OpenAI API key in `.env`
2. Set `QUIZ_GENERATION_STRATEGY=openai`
3. Test connectivity: `GET /test-openai`
4. Generate a quiz: `POST /quizzes/generate`

## Architecture

- **FastAPI**: Modern web framework
- **SQLAlchemy**: Database ORM
- **Celery**: Background task processing
- **Redis**: Caching and message broker
- **PostgreSQL**: Primary database
- **Event-Driven**: Real-time notifications and progress updates

## Dependencies

- `fastapi==0.104.1`
- `uvicorn==0.24.0`
- `openai==1.3.7`
- `httpx==0.25.2`
- `celery==5.3.4`
- `sqlalchemy==2.0.23`
- `redis==5.0.1`
