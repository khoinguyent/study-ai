# 🎯 Quiz Service - Quick Reference

## 🚀 **What is Quiz Service?**

The Quiz Service is the **AI-powered quiz generation engine** for the Study AI platform. It creates personalized educational quizzes based on documents, subjects, and categories using multiple AI backends.

## 🏗️ **Architecture Overview**

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   FastAPI App   │    │   Celery Tasks  │    │   Event System  │
│   (Main API)    │◄──►│  (Background)   │◄──►│ (Real-time)     │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│  AI Generators  │    │   PostgreSQL    │    │     Redis       │
│ OpenAI/HF/Ollama│    │   (Quiz Data)   │    │ (Cache/Events)  │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

## 🔧 **Key Components**

### 1. **Main Application** (`app/main.py`)
- **FastAPI web server** with REST endpoints
- **Authentication middleware** (JWT token verification)
- **Mock quiz generator** for development/testing
- **Study session management** endpoints

### 2. **Quiz Generator** (`app/services/quiz_generator.py`)
- **Multi-AI backend support**: OpenAI, HuggingFace, Ollama
- **Context-aware generation** from document chunks
- **JSON format enforcement** for consistent quiz structure
- **Smart fallback strategy** (auto mode)

### 3. **Data Models** (`app/models.py`)
- **`Quiz`**: Core quiz entity with questions, metadata
- **`CustomDocumentSet`**: User-defined document collections

### 4. **Background Tasks** (`app/tasks.py`)
- **Celery integration** for async quiz generation
- **Event publishing** for real-time progress updates
- **Task status tracking** and error handling

## 🎲 **AI Backends Supported**

| Backend | Model | Pros | Cons | Use Case |
|---------|-------|------|------|----------|
| **OpenAI** | GPT-3.5/4 | High quality, JSON format | Cost, API limits | Production |
| **HuggingFace** | Flan-T5 | Free, open source | Lower quality | Development |
| **Ollama** | Llama2:7b | Local, private | Resource intensive | Privacy-focused |

## ⚙️ **Configuration**

### **Environment Variables** (`.env`)
```bash
# Strategy Selection
QUIZ_GENERATION_STRATEGY=openai  # openai, huggingface, ollama, auto

# OpenAI (Recommended)
OPENAI_API_KEY=sk-...
OPENAI_MODEL=gpt-3.5-turbo
OPENAI_MAX_TOKENS=2000

# HuggingFace
HUGGINGFACE_TOKEN=hf_...
QUESTION_GENERATION_MODEL=google/flan-t5-base

# Ollama (Local)
OLLAMA_BASE_URL=http://ollama:11434
OLLAMA_MODEL=llama2:7b
```

## 🚦 **Quick Start Guide**

### **1. Setup Environment**
```bash
cd services/quiz-service
cp env.example .env
# Edit .env with your API keys
```

### **2. Install Dependencies**
```bash
pip install -r requirements.txt
```

### **3. Run Service**
```bash
# Local development
uvicorn app.main:app --reload --host 0.0.0.0 --port 8004

# Docker
docker-compose up quiz-service
```

### **4. Test Integration**
```bash
# Health check
curl http://localhost:8004/health

# Test OpenAI
curl http://localhost:8004/test-openai

# Test Ollama
curl http://localhost:8004/test-ollama
```

## 📡 **Key API Endpoints**

### **Health & Testing**
- `GET /health` - Service status
- `GET /test-openai` - OpenAI connectivity test
- `GET /test-ollama` - Ollama connectivity test

### **Study Sessions** (Main Flow)
- `POST /study-sessions/start` - Begin quiz generation
- `GET /study-sessions/status` - Check progress
- `GET /study-sessions/events` - Real-time updates
- `POST /study-sessions/confirm` - Generate final quiz

### **Direct Quiz Generation**
- `POST /quizzes/generate` - Generate quiz with auth
- `POST /quizzes/generate-simple` - Generate without auth (testing)

## 🔄 **Quiz Generation Flow**

```
1. User Request → 2. AI Processing → 3. Progress Updates → 4. Quiz Delivery
     ↓                    ↓                    ↓                    ↓
Start Session      AI Generates Qs      Real-time Events    Final Quiz
```

### **Detailed Flow:**
1. **Session Start**: User provides topic, difficulty, question count
2. **Context Preparation**: Document chunks are prepared for AI
3. **AI Generation**: Selected AI model creates questions
4. **Progress Tracking**: WebSocket events update frontend
5. **Quiz Assembly**: Questions formatted with options/explanations
6. **Delivery**: Complete quiz returned to user

## 🧪 **Development & Testing**

### **Mock Mode** (Default)
- Service currently uses mock data generation
- Real AI calls are commented out in `_generate_content()`
- To enable real AI: uncomment the strategy selection code

### **Testing Different AI Backends**
```bash
# Test OpenAI
QUIZ_GENERATION_STRATEGY=openai
curl -X POST http://localhost:8004/quizzes/generate-simple \
  -H "Content-Type: application/json" \
  -d '{"numQuestions": 5, "difficulty": "medium"}'

# Test HuggingFace
QUIZ_GENERATION_STRATEGY=huggingface

# Test Ollama
QUIZ_GENERATION_STRATEGY=ollama
```

## 🐛 **Common Issues & Solutions**

### **OpenAI API Errors**
- **401 Unauthorized**: Check API key in `.env`
- **Rate Limits**: Implement exponential backoff
- **Model Not Found**: Verify model name in config

### **HuggingFace Issues**
- **Token Required**: Set `HUGGINGFACE_TOKEN`
- **Model Loading**: Some models take time to load first time

### **Ollama Problems**
- **Connection Failed**: Check if Ollama service is running
- **Model Not Found**: Pull model with `ollama pull llama2:7b`

## 📊 **Monitoring & Debugging**

### **Logs**
- Service logs show AI backend selection
- API call responses and errors
- Task progress and completion

### **Health Checks**
- `/health` - Basic service status
- `/test-*` - Backend connectivity tests
- Database connection status

## 🔮 **Future Enhancements**

- **Question Type Expansion**: Essay, matching, ordering
- **Difficulty Calibration**: Adaptive question generation
- **Multi-language Support**: Internationalization
- **Analytics Dashboard**: Quiz performance metrics
- **A/B Testing**: Different AI strategies comparison

## 📚 **Related Documentation**

- `README.md` - Comprehensive service documentation
- `env.example` - Environment configuration template
- `app/config.py` - Configuration class definition
- `app/services/quiz_generator.py` - AI integration logic

---

**Quick Command Reference:**
```bash
# Start service
uvicorn app.main:app --reload --port 8004

# Test OpenAI
curl http://localhost:8004/test-openai

# Generate quiz
curl -X POST http://localhost:8004/quizzes/generate-simple \
  -H "Content-Type: application/json" \
  -d '{"numQuestions": 3}'

# Check health
curl http://localhost:8004/health
```

**Need Help?** Check the main `README.md` for detailed information! 🚀
