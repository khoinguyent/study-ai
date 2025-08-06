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
- AWS S3 bucket for document storage
- OpenAI API key for quiz generation

### Development Environment Setup

1. **Clone and setup the repository:**
   ```bash
   git clone <repository-url>
   cd study-ai
   ```

2. **Configure environment variables:**
   ```bash
   # Copy example environment files
   cp services/auth-service/.env.example services/auth-service/.env
   cp services/document-service/.env.example services/document-service/.env
   cp services/quiz-service/.env.example services/quiz-service/.env
   
   # Edit the .env files with your actual values
   ```

3. **Start all services:**
   ```bash
   docker-compose up -d
   ```

4. **Verify services are running:**
   ```bash
   docker-compose ps
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

1. Start the backend server
2. Start the web development server
3. Start the mobile development server

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