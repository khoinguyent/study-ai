#!/bin/bash

# Docker Compose Troubleshooting Script for Study AI Platform
# This script helps diagnose and fix common Docker Compose issues

set -e

echo "🔍 Docker Compose Troubleshooting Script"
echo "========================================"

# Check if Docker is running
echo "📋 Checking Docker status..."
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker is not running. Please start Docker Desktop first."
    exit 1
fi
echo "✅ Docker is running"

# Check Docker Compose version
echo "📋 Checking Docker Compose version..."
docker-compose --version
echo ""

# Stop all containers and clean up
echo "🧹 Cleaning up existing containers..."
docker-compose down -v --remove-orphans
docker system prune -f

# Check available disk space
echo "📊 Checking disk space..."
df -h | grep -E "(Filesystem|/dev/)"
echo ""

# Check Docker daemon logs
echo "📋 Checking Docker daemon logs..."
if [[ "$OSTYPE" == "darwin"* ]]; then
    # macOS
    echo "macOS detected - checking Docker Desktop logs..."
    if [ -f ~/Library/Containers/com.docker.docker/Data/log/vm/dockerd.log ]; then
        echo "Last 10 lines of Docker daemon log:"
        tail -10 ~/Library/Containers/com.docker.docker/Data/log/vm/dockerd.log
    else
        echo "Docker daemon log not found at expected location"
    fi
else
    # Linux
    echo "Linux detected - checking Docker daemon logs..."
    sudo journalctl -u docker.service --no-pager -n 10
fi
echo ""

# Check if required ports are available
echo "🔌 Checking port availability..."
ports=(8000 8001 8002 8003 8004 8005 8010 8011 5432 5433 5434 5435 5437 6379 9000 9001 11434 3001)
for port in "${ports[@]}"; do
    if lsof -Pi :$port -sTCP:LISTEN -t >/dev/null 2>&1; then
        echo "⚠️  Port $port is already in use"
    else
        echo "✅ Port $port is available"
    fi
done
echo ""

# Check environment variables
echo "🔧 Checking environment variables..."
if [ -f .env.local ]; then
    echo "✅ .env.local file found"
    echo "📋 Checking critical environment variables:"
    if grep -q "OPENAI_API_KEY" .env.local; then
        echo "✅ OPENAI_API_KEY is set"
    else
        echo "⚠️  OPENAI_API_KEY is not set"
    fi
    if grep -q "HUGGINGFACE_TOKEN" .env.local; then
        echo "✅ HUGGINGFACE_TOKEN is set"
    else
        echo "⚠️  HUGGINGFACE_TOKEN is not set"
    fi
else
    echo "⚠️  .env.local file not found - creating from example..."
    if [ -f env.local.example ]; then
        cp env.local.example .env.local
        echo "✅ .env.local created from example"
        echo "⚠️  Please update .env.local with your actual API keys"
    else
        echo "❌ env.local.example not found"
    fi
fi
echo ""

# Try to start services step by step
echo "🚀 Starting services step by step..."

# Start databases first
echo "📊 Starting databases..."
docker-compose up -d auth-db document-db indexing-db quiz-db notification-db redis minio
echo "⏳ Waiting for databases to be healthy..."
sleep 30

# Check database health
echo "📋 Checking database health..."
docker-compose ps | grep -E "(db|redis|minio)"
echo ""

# Start core services
echo "🔧 Starting core services..."
docker-compose up -d auth-service
echo "⏳ Waiting for auth service..."
sleep 20

docker-compose up -d document-service
echo "⏳ Waiting for document service..."
sleep 20

docker-compose up -d indexing-service
echo "⏳ Waiting for indexing service..."
sleep 20

docker-compose up -d quiz-service
echo "⏳ Waiting for quiz service..."
sleep 20

docker-compose up -d notification-service
echo "⏳ Waiting for notification service..."
sleep 20

# Start workers
echo "👷 Starting workers..."
docker-compose up -d document-worker indexing-worker quiz-worker
echo "⏳ Waiting for workers to start..."
sleep 30

# Check all services
echo "📋 Checking all services..."
docker-compose ps
echo ""

# Check worker logs specifically
echo "📋 Checking document-worker logs..."
docker-compose logs document-worker --tail=20
echo ""

echo "📋 Checking indexing-worker logs..."
docker-compose logs indexing-worker --tail=20
echo ""

echo "📋 Checking quiz-worker logs..."
docker-compose logs quiz-worker --tail=20
echo ""

# Check network connectivity
echo "🌐 Checking network connectivity..."
echo "📋 Testing inter-service communication..."
docker-compose exec document-worker ping -c 3 redis
docker-compose exec document-worker ping -c 3 document-db
docker-compose exec document-worker ping -c 3 minio

echo ""
echo "🎯 Troubleshooting complete!"
echo ""
echo "If you still have issues:"
echo "1. Check the logs above for specific error messages"
echo "2. Ensure all required environment variables are set in .env.local"
echo "3. Try restarting Docker Desktop"
echo "4. Check if your system has enough resources (RAM, CPU, disk space)"
echo ""
echo "To view real-time logs:"
echo "docker-compose logs -f [service-name]"
echo ""
echo "To restart a specific service:"
echo "docker-compose restart [service-name]"
