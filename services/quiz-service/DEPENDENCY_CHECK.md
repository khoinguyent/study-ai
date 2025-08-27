# Quiz Service Dependency Check

## Overview
This document lists all dependencies required for the quiz-service to build and run successfully in Docker.

## Python Dependencies (requirements.txt)

### Core Framework
- ✅ `fastapi==0.104.1` - Web framework
- ✅ `uvicorn==0.24.0` - ASGI server
- ✅ `sqlalchemy==2.0.23` - Database ORM
- ✅ `psycopg2-binary==2.9.9` - PostgreSQL adapter
- ✅ `pydantic==2.5.0` - Data validation
- ✅ `pydantic-settings==2.1.0` - Settings management

### Authentication & Security
- ✅ `python-jose[cryptography]==3.3.0` - JWT handling
- ✅ `passlib[bcrypt]==1.7.4` - Password hashing
- ✅ `PyJWT==2.8.0` - JWT library
- ✅ `jwt==1.3.1` - JWT utilities

### HTTP & API
- ✅ `python-multipart==0.0.6` - Form data handling
- ✅ `httpx==0.25.2` - HTTP client
- ✅ `requests==2.32.3` - HTTP library

### Background Processing
- ✅ `redis==5.0.1` - Redis client
- ✅ `celery==5.3.4` - Task queue

### AI/ML Dependencies
- ✅ `openai==1.3.7` - OpenAI API client
- ✅ `numpy==1.25.2` - Numerical computing
- ✅ `pandas==2.1.4` - Data manipulation

### Template Engine
- ✅ `jinja2==3.1.4` - Template rendering

### Language Detection
- ✅ `lingua-language-detector==2.0.2` - Primary language detection
- ✅ `pycld3==0.22` - Google's language detection
- ✅ `langdetect==1.0.9` - Fallback language detection

## System Dependencies (Dockerfile)

### Base Image
- ✅ `python:3.11-slim` - Python runtime

### Build Tools
- ✅ `gcc` - C compiler
- ✅ `g++` - C++ compiler
- ✅ `build-essential` - Essential build tools

### Development Libraries
- ✅ `libffi-dev` - Foreign function interface
- ✅ `libssl-dev` - SSL/TLS development

## Import Dependencies

### Core App Modules
- ✅ `app.config` - Configuration settings
- ✅ `app.database` - Database connection
- ✅ `app.models` - Data models
- ✅ `app.schemas` - Pydantic schemas

### New Generator System
- ✅ `app.generator.orchestrator` - Main orchestration
- ✅ `app.generator.context_builder` - Context management
- ✅ `app.generator.validators` - Validation logic

### LLM Providers
- ✅ `app.llm.providers.base` - Provider interface
- ✅ `app.llm.providers.openai_adapter` - OpenAI integration
- ✅ `app.llm.providers.ollama_adapter` - Ollama integration
- ✅ `app.llm.providers.hf_adapter` - HuggingFace integration

### Language Detection
- ✅ `app.lang.detect` - Language detection logic
- ✅ `app.lang.language` - Language utilities

## Database Models

### Required Models
- ✅ `Quiz` - Quiz storage
- ✅ `CustomDocumentSet` - Document set management
- ✅ `QuestionBank` - Question storage with LLM traces

### Model Dependencies
- ✅ `QUESTION_TYPE` enum - Question type definitions
- ✅ `DIFFICULTY` enum - Difficulty level definitions

## Potential Issues & Solutions

### 1. Language Detection Libraries
**Issue**: `lingua-language-detector` and `pycld3` require system-level dependencies
**Solution**: Added `gcc`, `g++`, `build-essential` to Dockerfile

### 2. Model Import Circular Dependencies
**Issue**: Models defined in multiple locations
**Solution**: Centralized model imports in `app/models/__init__.py`

### 3. JWT Library Duplication
**Issue**: Both `PyJWT` and `jwt` packages
**Solution**: Both are needed for different use cases

### 4. Database Connection
**Issue**: PostgreSQL dependency
**Solution**: `psycopg2-binary` included for PostgreSQL support

## Testing

### Local Testing
```bash
cd services/quiz-service
python3 test_docker_build.py
```

### Docker Testing
```bash
cd services/quiz-service
./build_test.sh
```

## Build Commands

### Docker Build
```bash
docker build -t quiz-service .
```

### Docker Run
```bash
docker run -p 8004:8004 quiz-service
```

## Health Check
The service exposes a health check endpoint at `/health` to verify it's running correctly.

## Notes

1. **Language Detection**: The system gracefully falls back if language detection libraries fail to load
2. **LLM Providers**: All providers are optional and the system works with any combination
3. **Database**: Requires PostgreSQL connection (configured via environment variables)
4. **Port**: Service runs on port 8004 by default

## Status: ✅ READY FOR DOCKER BUILD

All dependencies are properly configured and the service should build successfully in Docker.
