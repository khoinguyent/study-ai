#!/bin/bash

# Study AI Local Development Setup Script

echo "🚀 Setting up Study AI Local Development Environment..."

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo -e "${RED}❌ Docker is not running. Please start Docker and try again.${NC}"
    exit 1
fi

# Check if .env file exists
if [ ! -f .env ]; then
    echo -e "${YELLOW}📝 Creating .env file from template...${NC}"
    cp env.example .env
    echo -e "${GREEN}✅ .env file created${NC}"
    echo -e "${YELLOW}⚠️  Please review and update .env file with your settings${NC}"
else
    echo -e "${GREEN}✅ .env file already exists${NC}"
fi

# Create necessary directories
echo "📁 Creating necessary directories..."
mkdir -p backend/uploads
mkdir -p backend/models
mkdir -p nginx/logs

# Pull and start MinIO and Ollama
echo "🐳 Starting MinIO and Ollama services..."
docker-compose up -d minio ollama

# Wait for services to be ready
echo "⏳ Waiting for MinIO and Ollama to be ready..."
sleep 10

# Check MinIO health
echo "🏥 Checking MinIO health..."
if curl -f http://localhost:9000/minio/health/live > /dev/null 2>&1; then
    echo -e "${GREEN}✅ MinIO is ready${NC}"
    echo -e "${YELLOW}📊 MinIO Console: http://localhost:9001${NC}"
    echo -e "${YELLOW}   Username: minioadmin${NC}"
    echo -e "${YELLOW}   Password: minioadmin${NC}"
else
    echo -e "${RED}❌ MinIO is not ready${NC}"
fi

# Check Ollama health
echo "🏥 Checking Ollama health..."
if curl -f http://localhost:11434/api/tags > /dev/null 2>&1; then
    echo -e "${GREEN}✅ Ollama is ready${NC}"
    echo -e "${YELLOW}🤖 Ollama API: http://localhost:11434${NC}"
else
    echo -e "${RED}❌ Ollama is not ready${NC}"
fi

# Download Llama2 model for Ollama (optional)
echo "📥 Setting up Llama2 model for Ollama..."
echo -e "${YELLOW}This will download a ~4GB model. Continue? (y/n)${NC}"
read -r response
if [[ "$response" =~ ^([yY][eE][sS]|[yY])$ ]]; then
    echo "📥 Downloading Llama2 model..."
    curl -X POST http://localhost:11434/api/pull -d '{"name": "llama2"}'
    echo -e "${GREEN}✅ Llama2 model downloaded${NC}"
else
    echo -e "${YELLOW}⚠️  Skipping model download. You can download it later with:${NC}"
    echo -e "${YELLOW}   curl -X POST http://localhost:11434/api/pull -d '{\"name\": \"llama2\"}'${NC}"
fi

# Build and start all services
echo "🔨 Building and starting all services..."
docker-compose up --build -d

# Wait for all services to be ready
echo "⏳ Waiting for all services to be ready..."
sleep 15

# Check service health
echo "🏥 Checking service health..."

# Check database
if docker-compose exec -T database pg_isready -U postgres > /dev/null 2>&1; then
    echo -e "${GREEN}✅ Database is ready${NC}"
else
    echo -e "${RED}❌ Database is not ready${NC}"
fi

# Check Redis
if docker-compose exec -T redis redis-cli ping > /dev/null 2>&1; then
    echo -e "${GREEN}✅ Redis is ready${NC}"
else
    echo -e "${RED}❌ Redis is not ready${NC}"
fi

# Check backend
if curl -f http://localhost/api/health > /dev/null 2>&1; then
    echo -e "${GREEN}✅ Backend API is ready${NC}"
else
    echo -e "${RED}❌ Backend API is not ready${NC}"
fi

echo ""
echo -e "${GREEN}🎉 Study AI Local Development Environment is ready!${NC}"
echo ""
echo "📋 Service URLs:"
echo -e "   🌐 Web Interface: ${GREEN}http://localhost${NC}"
echo -e "   🔧 Backend API: ${GREEN}http://localhost/api${NC}"
echo -e "   📊 Health Check: ${GREEN}http://localhost/api/health${NC}"
echo -e "   📦 MinIO Console: ${GREEN}http://localhost:9001${NC}"
echo -e "   🤖 Ollama API: ${GREEN}http://localhost:11434${NC}"
echo ""
echo "🔧 Services running:"
echo "   - PostgreSQL Database (port 5432)"
echo "   - Redis Cache (port 6379)"
echo "   - MinIO Object Storage (port 9000)"
echo "   - Ollama LLM (port 11434)"
echo "   - Flask Backend with Gunicorn"
echo "   - Celery Worker (background tasks)"
echo "   - Celery Beat (scheduled tasks)"
echo "   - Nginx Reverse Proxy (port 80)"
echo ""
echo "📝 Useful Commands:"
echo "   View logs: docker-compose logs -f"
echo "   Stop services: docker-compose down"
echo "   Restart services: docker-compose restart"
echo "   Test API: ./test-api.sh"
echo ""
echo "🔑 MinIO Credentials:"
echo "   Username: minioadmin"
echo "   Password: minioadmin"
echo ""
echo "🤖 Ollama Models:"
echo "   Available models: curl http://localhost:11434/api/tags"
echo "   Download model: curl -X POST http://localhost:11434/api/pull -d '{\"name\": \"llama2\"}'"
echo "" 