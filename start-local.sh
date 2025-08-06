#!/bin/bash

# Study AI Local Development Startup Script

echo "🚀 Starting Study AI Local Development Environment..."

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker is not running. Please start Docker and try again."
    exit 1
fi

# Check if .env file exists
if [ ! -f .env ]; then
    echo "📝 Creating .env file from template..."
    cp env.example .env
    echo "⚠️  Please update .env file with your OpenAI API key and other settings"
fi

# Create necessary directories
echo "📁 Creating necessary directories..."
mkdir -p backend/uploads
mkdir -p nginx/logs

# Build and start services
echo "🔨 Building and starting services..."
docker-compose up --build -d

# Wait for services to be ready
echo "⏳ Waiting for services to be ready..."
sleep 10

# Check service health
echo "🏥 Checking service health..."

# Check database
if docker-compose exec -T database pg_isready -U postgres > /dev/null 2>&1; then
    echo "✅ Database is ready"
else
    echo "❌ Database is not ready"
fi

# Check Redis
if docker-compose exec -T redis redis-cli ping > /dev/null 2>&1; then
    echo "✅ Redis is ready"
else
    echo "❌ Redis is not ready"
fi

# Check backend
if curl -f http://localhost/api/health > /dev/null 2>&1; then
    echo "✅ Backend API is ready"
else
    echo "❌ Backend API is not ready"
fi

echo ""
echo "🎉 Study AI is now running locally!"
echo ""
echo "📋 Service URLs:"
echo "   🌐 Web Interface: http://localhost"
echo "   🔧 Backend API: http://localhost/api"
echo "   📊 Health Check: http://localhost/api/health"
echo ""
echo "📝 Useful Commands:"
echo "   View logs: docker-compose logs -f"
echo "   Stop services: docker-compose down"
echo "   Restart services: docker-compose restart"
echo "   View specific service logs: docker-compose logs -f [service-name]"
echo ""
echo "🔧 Services running:"
echo "   - PostgreSQL Database (port 5432)"
echo "   - Redis Cache (port 6379)"
echo "   - Flask Backend with Gunicorn"
echo "   - Celery Worker (background tasks)"
echo "   - Celery Beat (scheduled tasks)"
echo "   - Nginx Reverse Proxy (port 80)"
echo "" 