# Study AI

A comprehensive AI-powered study platform with backend, web, and mobile applications.

## 🚀 Project Structure

```
study-ai/
├── backend/          # Server-side application
├── web/             # Web frontend application
├── mobile/          # Mobile application
└── README.md        # This file
```

## 📋 Prerequisites

- Node.js (v18 or higher)
- npm or yarn
- Git

## 🛠️ Getting Started

### Prerequisites

- Docker and Docker Compose
- Git
- OpenAI API key (for AI features)

### Quick Start (Recommended)

1. **Clone and setup environment:**
   ```bash
   git clone <your-repo-url>
   cd study-ai
   cp env.example .env
   # Edit .env file with your OpenAI API key
   ```

2. **Start the entire stack:**
   ```bash
   ./start-local.sh
   ```

3. **Test the API:**
   ```bash
   ./test-api.sh
   ```

4. **Access the application:**
   - Web Interface: http://localhost
   - API Health Check: http://localhost/api/health
   - Backend API: http://localhost/api

### Manual Setup

#### Backend Setup

```bash
cd backend
pip install -r requirements.txt
python app.py
```

#### Database Setup

```bash
# Using Docker Compose
docker-compose up database redis -d

# Or manually
docker run -d --name study-ai-db \
  -e POSTGRES_DB=study_ai \
  -e POSTGRES_USER=postgres \
  -e POSTGRES_PASSWORD=password \
  -p 5432:5432 \
  postgres:15

docker run -d --name study-ai-redis \
  -p 6379:6379 \
  redis:7-alpine
```

#### Web Frontend Setup

```bash
cd web
# Add your web frontend setup instructions here
```

#### Mobile App Setup

```bash
cd mobile
# Add your mobile app setup instructions here
```

## 🏗️ Architecture

This project follows a **EC2 + Docker + Nginx + Gunicorn + Celery + Redis** architecture:

### Components

- **Amazon EC2 Instance**: Virtual server hosting the entire application
- **Docker**: Containerization for consistent deployment across environments
- **Nginx**: High-performance reverse proxy handling HTTP requests
- **Gunicorn**: Production-grade WSGI server for Python Flask application
- **Celery**: Distributed task queue for background processing
- **Redis**: Message broker for Celery and caching layer
- **PostgreSQL**: Primary database for application data

### Service Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Client/Browser│    │   Mobile App    │    │   API Client    │
└─────────┬───────┘    └─────────┬───────┘    └─────────┬───────┘
          │                      │                      │
          └──────────────────────┼──────────────────────┘
                                 │
                    ┌─────────────▼─────────────┐
                    │        Nginx (Port 80)    │
                    │     Reverse Proxy         │
                    └─────────────┬─────────────┘
                                  │
                    ┌─────────────▼─────────────┐
                    │    Flask + Gunicorn       │
                    │    (Port 5000)            │
                    └─────────────┬─────────────┘
                                  │
          ┌───────────────────────┼───────────────────────┐
          │                       │                       │
┌─────────▼─────────┐    ┌────────▼────────┐    ┌────────▼────────┐
│   PostgreSQL      │    │     Redis       │    │   Celery Worker │
│   Database        │    │   Cache/Broker  │    │  Background     │
└───────────────────┘    └─────────────────┘    └─────────────────┘
```

### Local Development

For local development, all services run in Docker containers:

- **Backend**: Flask application with Gunicorn
- **Web**: React/Vue.js frontend application
- **Mobile**: React Native/Flutter mobile application

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