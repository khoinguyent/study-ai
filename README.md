# Study AI Platform

A comprehensive AI-powered study platform with document processing, quiz generation, and intelligent clarification flows.

## 📚 **Documentation**

For complete documentation, see: **[STUDY_AI_COMPREHENSIVE_GUIDE.md](./STUDY_AI_COMPREHENSIVE_GUIDE.md)**

## 🚀 **Quick Start**

### Prerequisites
- Docker and Docker Compose
- Node.js 18+ (for frontend development)
- Python 3.9+ (for backend development)

### Start the Platform
```bash
# Clone the repository
git clone <repository-url>
cd study-ai

# Start all services
docker-compose up -d

# Access the platform
# Frontend: http://localhost:3001
# API Gateway: http://localhost:8000
```

### Development
```bash
# Setup development environment
./scripts/setup-dev.sh

# Run tests
./test-quiz-generation.sh

# Monitor logs
docker-compose logs -f
```

## 🏗️ **Architecture Overview**

### Core Services
- **API Gateway** (port 8000) - Main entry point and routing
- **Auth Service** (port 8001) - Authentication and user management
- **Document Service** (port 8002) - Document upload and management
- **Indexing Service** (port 8003) - Document indexing and search
- **Quiz Service** (port 8004) - Quiz generation and management
- **Notification Service** (port 8005) - Real-time notifications
- **Clarifier Service** (port 8010) - Extensible clarification flows
- **Question Budget Service** (port 8011) - Question count calculation

### Key Features
- **Document Upload & Processing**: Intelligent chunking and indexing
- **AI-Powered Quiz Generation**: Multiple question types with real-time generation
- **Real-time Notifications**: SSE-based progress tracking and completion alerts
- **Multi-language Support**: LaBSE-based vector search and embedding
- **Extensible Clarification Flows**: Slot-filling engine for user input collection

## 🔧 **Recent Updates**

### Quiz Toast System Fixes ✅
- Fixed duplicate toast notifications
- Resolved SSE MIME type errors
- Added proper quiz completion event handling
- Improved real-time progress tracking

### Question Data Structure Update ✅
- Standardized question types with "type" field
- Updated data structures across frontend and backend
- Improved type safety and consistency

### Comprehensive Documentation ✅
- Merged all documentation into single comprehensive guide
- Added detailed API reference
- Included troubleshooting and development workflows

## 📖 **Documentation Sections**

The comprehensive guide includes:

1. **Platform Overview** - Core features and capabilities
2. **Architecture** - Service architecture and infrastructure
3. **Quiz Generation System** - Complete quiz generation workflow
4. **Quiz Toast System** - Real-time notification system
5. **Document Processing** - Intelligent document chunking and indexing
6. **Clarifier Service** - Extensible clarification flows
7. **Infrastructure & Deployment** - Multi-environment deployment
8. **Development Workflow** - Development and testing procedures
9. **Troubleshooting** - Common issues and solutions
10. **API Reference** - Complete API documentation

## 🤝 **Contributing**

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Run tests: `./test-quiz-generation.sh`
5. Submit a pull request

## 📄 **License**

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

**For detailed documentation, architecture diagrams, and complete API reference, see [STUDY_AI_COMPREHENSIVE_GUIDE.md](./STUDY_AI_COMPREHENSIVE_GUIDE.md)**