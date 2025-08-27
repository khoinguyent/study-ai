# Quiz Service

## Overview

The Quiz Service is a microservice that generates AI-powered quizzes using multiple LLM providers (OpenAI, Ollama, Hugging Face). It implements a Direct Chunks Generator that works directly with document chunks without relying on OpenAI File Search.

## Features

- 🚀 **Multi-LLM Support**: OpenAI, Ollama, and Hugging Face
- 📚 **Direct Chunks Generation**: Uses document chunks directly from database
- 🌍 **Language Auto-Detection**: Automatically detects and enforces output language
- ✅ **Validation Pipeline**: JSON structure, citations, and type validation
- 🔄 **Repair System**: Automatic repair attempts for failed generations
- 📊 **LLM Trace Storage**: Complete metadata for all generated questions
- 🐳 **Docker Ready**: Fully containerized with all dependencies

## Quick Start

### Using Docker (Recommended)

```bash
# Build the service
docker build -t quiz-service .

# Run the service
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
GET /test-ollama    # Test Ollama connectivity
GET /test-openai    # Test OpenAI connectivity
```

### Quiz Generation
```
POST /generate-quiz
POST /generate-quiz-from-subject
POST /generate-quiz-from-category
```

## Configuration

### Environment Variables

```bash
# Database
DATABASE_URL=postgresql://user:pass@localhost/quizdb

# LLM Providers
OPENAI_API_KEY=your_openai_key
OLLAMA_BASE_URL=http://localhost:11434
HF_API_KEY=your_huggingface_key

# Service Settings
QUIZ_GENERATION_STRATEGY=auto  # auto, openai, ollama, huggingface
```

## Architecture

### Core Components

1. **QuizGenerator Service** (`app/services/quiz_generator.py`)
   - Main service class with multiple generation strategies
   - Integrates with new Direct Chunks Generator

2. **Direct Chunks Generator** (`app/generator/`)
   - `orchestrator.py` - Main generation flow
   - `context_builder.py` - Document chunk management
   - `validators.py` - Validation and repair logic

3. **LLM Providers** (`app/llm/providers/`)
   - `base.py` - Common interface
   - `openai_adapter.py` - OpenAI integration
   - `ollama_adapter.py` - Ollama integration
   - `hf_adapter.py` - HuggingFace integration

4. **Language Detection** (`app/lang/`)
   - `detect.py` - Multi-library language detection
   - `language.py` - Language utilities

### Data Flow

1. **Document Selection** → User selects documents to generate questions from
2. **Chunk Fetching** → System fetches relevant chunks from database
3. **Context Curation** → Chunks are curated and prepared for prompts
4. **Language Detection** → System detects language from chunk content
5. **Prompt Generation** → Jinja2 templates render prompts with context
6. **LLM Generation** → Selected provider generates questions
7. **Validation** → JSON structure, citations, and language are validated
8. **Storage** → Questions are saved with complete LLM traces

## Usage Examples

### Basic Quiz Generation

```python
from app.services.quiz_generator import QuizGenerator

generator = QuizGenerator()

# Generate quiz from documents
quiz_data = await generator.generate_quiz_from_documents_direct(
    session=db_session,
    subject_name="Vietnamese History",
    doc_ids=[1, 2, 3],
    total_count=10,
    allowed_types=["MCQ", "TF"],
    budget_cap=10
)
```

### Using Different LLM Providers

```python
from app.llm.providers.ollama_adapter import OllamaProvider
from app.generator.orchestrator import generate_from_documents

# Create provider
provider = OllamaProvider(base_url="http://localhost:11434", model="llama3")

# Generate directly
batch, blocks, lang_code = generate_from_documents(
    session=db_session,
    provider=provider,
    subject_name="Mathematics",
    doc_ids=[1, 2],
    total_count=5,
    allowed_types=["MCQ"]
)
```

## Testing

### Run Tests

```bash
# Test dependencies
python3 test_docker_build.py

# Test Docker build
./build_test.sh

# Test direct generator
python3 test_direct_generator.py
```

### Test Coverage

- ✅ Import tests
- ✅ Language detection
- ✅ Provider creation
- ✅ Docker build
- ✅ Service startup

## Dependencies

### Python Packages
- **Framework**: FastAPI, Uvicorn, SQLAlchemy
- **AI/ML**: OpenAI, NumPy, Pandas
- **Language**: Jinja2, Lingua, pycld3
- **Database**: psycopg2-binary, Redis
- **Background**: Celery

### System Dependencies
- **Build Tools**: gcc, g++, build-essential
- **Libraries**: libffi-dev, libssl-dev

## Troubleshooting

### Common Issues

1. **Language Detection Fails**
   - Check if `lingua-language-detector` and `pycld3` are installed
   - Verify system dependencies in Dockerfile

2. **Import Errors**
   - Ensure all Python packages are installed
   - Check Python path configuration

3. **Database Connection**
   - Verify PostgreSQL is running
   - Check `DATABASE_URL` environment variable

4. **LLM Provider Issues**
   - Verify API keys and endpoints
   - Check network connectivity

### Debug Mode

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

## Development

### Project Structure

```
app/
├── generator/           # Direct chunks generator
│   ├── orchestrator.py
│   ├── context_builder.py
│   └── validators.py
├── llm/                # LLM provider adapters
│   └── providers/
├── lang/               # Language detection
├── models/             # Database models
├── services/           # Business logic
└── main.py            # FastAPI application
```

### Adding New LLM Providers

1. Create new adapter in `app/llm/providers/`
2. Implement `LLMProvider` protocol
3. Add to provider selection logic
4. Update tests and documentation

## Contributing

1. Follow the existing code structure
2. Add tests for new functionality
3. Update documentation
4. Ensure Docker build passes

## License

This project is part of the Study AI platform.

## Support

For issues and questions, please check the troubleshooting section or create an issue in the project repository.
