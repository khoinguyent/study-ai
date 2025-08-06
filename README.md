# Study AI

A comprehensive AI-powered study platform built with microservices architecture, featuring backend, web, and mobile applications.

## 🚀 Project Structure

```
study-ai/
├── services/                    # Microservices
│   ├── api-gateway/            # Nginx API Gateway
│   ├── auth-service/           # Authentication & User Management
│   ├── document-service/       # Document Upload & Processing
│   ├── indexing-service/       # Vector Indexing & Search
│   └── quiz-service/           # AI Quiz Generation
├── web/                        # Web frontend application
├── mobile/                     # Mobile application
├── docker-compose.yml          # Development environment
└── README.md                   # This file
```

## 📋 Prerequisites

- Node.js (v18 or higher)
- npm or yarn
- Git

## 🛠️ Getting Started

### Prerequisites

- Docker and Docker Compose
- Node.js (v18 or higher) for web/mobile development
- Python 3.11+ for local development

### Development vs Production

**Development Environment:**
- **MinIO** instead of AWS S3 (local S3-compatible storage)
- **Ollama** instead of OpenAI (local LLM)
- **Real-time notifications** via WebSocket
- **Async task processing** with progress tracking

**Production Environment:**
- **AWS S3** for document storage
- **OpenAI GPT** for quiz generation
- **Redis** for caching and message queuing

### Development Environment Setup

1. **Clone and setup the repository:**
   ```bash
   git clone <repository-url>
   cd study-ai
   ```

2. **Quick setup (recommended):**
   ```bash
   # This will set up everything automatically
   ./scripts/setup-dev.sh
   ```

3. **Manual setup (alternative):**
   ```bash
   # Start development services
   docker-compose -f docker-compose.dev.yml up -d
   
   # Create test data
   ./scripts/seed_data_docker.sh
   
   # Test the setup
   ./scripts/test_login.sh
   ```

4. **Verify services are running:**
   ```bash
   docker-compose -f docker-compose.dev.yml ps
   ```

### Individual Service Setup

#### Auth Service
```bash
cd services/auth-service
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8001
```

#### Document Service
```bash
cd services/document-service
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8002
```

#### Indexing Service
```bash
cd services/indexing-service
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8003
```

#### Quiz Service
```bash
cd services/quiz-service
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8004
```

### Web Frontend Setup

```bash
cd web
npm install
npm start
```

### Mobile App Setup

```bash
cd mobile
npm install
npx react-native run-ios  # or run-android
```

## 🏗️ Architecture

### Microservices Architecture

- **API Gateway**: Nginx-based gateway for routing and authentication
- **Auth Service**: User authentication, registration, and JWT token management
- **Document Service**: File upload, processing, and S3 storage management
- **Indexing Service**: Document chunking, vector embeddings, and similarity search
- **Quiz Service**: AI-powered quiz generation using LLMs and RAG
- **Web**: React/Vue.js frontend application
- **Mobile**: React Native/Flutter mobile application

### Technology Stack

- **Backend**: FastAPI, PostgreSQL, Redis, Celery
- **AI/ML**: OpenAI GPT, Sentence Transformers, pgvector
- **Storage**: AWS S3, PostgreSQL with pgvector extension
- **Message Queue**: Redis + Celery
- **API Gateway**: Nginx
- **Containerization**: Docker & Docker Compose

## 🔧 Development

### Running the Development Environment

1. **Start all services:**
   ```bash
   docker-compose up -d
   ```

2. **Create test data:**
   ```bash
   # Option 1: Using Docker (recommended)
   ./scripts/seed_data_docker.sh
   
   # Option 2: Using local Python
   ./scripts/seed_test_data.sh
   ```

3. **Test the login functionality:**
   ```bash
   ./scripts/test_login.sh
   ```

4. **Access the services:**
   - API Gateway: http://localhost
   - Auth Service: http://localhost:8001/docs
   - Document Service: http://localhost:8002/docs
   - Indexing Service: http://localhost:8003/docs
   - Quiz Service: http://localhost:8004/docs
   - Notification Service: http://localhost:8005/docs
   - Web Frontend: http://localhost:3001

5. **Development Tools:**
   - MinIO Console: http://localhost:9001 (minioadmin/minioadmin)
   - Ollama API: http://localhost:11434

### Test Data

The application comes with pre-configured test users:

**Primary Test User:**
- Email: `test@test.com`
- Password: `test123`
- Username: `testuser`

**Additional Test Users:**
- Email: `admin@study-ai.com` | Password: `admin123`
- Email: `student@study-ai.com` | Password: `student123`
- Email: `teacher@study-ai.com` | Password: `teacher123`
- Email: `demo@study-ai.com` | Password: `demo123`

### Quick Test Commands

```bash
# Test login directly to Auth Service
curl -X POST http://localhost:8001/login \
  -H 'Content-Type: application/json' \
  -d '{"email": "test@test.com", "password": "test123"}'

# Test login through API Gateway
curl -X POST http://localhost/auth/login \
  -H 'Content-Type: application/json' \
  -d '{"email": "test@test.com", "password": "test123"}'

# Test Ollama (local LLM)
curl -X POST http://localhost:11434/api/generate \
  -H 'Content-Type: application/json' \
  -d '{"model": "llama2", "prompt": "Hello, how are you?"}'

# Test WebSocket notifications (using wscat or similar tool)
wscat -c ws://localhost/ws/test@test.com
```

### Building for Production

Instructions for building each component for production deployment.

## 📱 Features

- [ ] Feature 1
- [ ] Feature 2
- [ ] Feature 3

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 📞 Support

For support, email support@study-ai.com or create an issue in this repository.

## 🔄 Version History

- **v1.0.0** - Initial release
  - Basic project structure
  - Backend, web, and mobile directories

---

**Note**: This is a template README. Update the content with your specific project details, setup instructions, and features. 