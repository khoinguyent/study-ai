#!/bin/bash

# Build and Start Script for Study AI Platform
# This script builds and starts all services with proper error handling

set -e  # Exit on any error

echo "🚀 Starting Study AI Platform build and deployment..."

# Check if Docker is running
echo "🔍 Checking Docker status..."
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker is not running. Please start Docker Desktop and try again."
    exit 1
fi

echo "✅ Docker is running"

# Clean up any existing containers
echo "🧹 Cleaning up existing containers..."
docker-compose down --remove-orphans || true

# Remove any dangling images
echo "🗑️  Cleaning up dangling images..."
docker image prune -f || true

# Build all services
echo "🔨 Building all services..."
docker-compose build --no-cache

# Check if build was successful
if [ $? -ne 0 ]; then
    echo "❌ Build failed. Please check the error messages above."
    exit 1
fi

echo "✅ All services built successfully"

# Start the infrastructure services first
echo "🚀 Starting infrastructure services (databases, Redis, MinIO)..."
docker-compose up -d auth-db document-db indexing-db quiz-db notification-db redis minio ollama

# Wait for infrastructure services to be healthy
echo "⏳ Waiting for infrastructure services to be healthy..."
sleep 30

# Start the core services
echo "🚀 Starting core services..."
docker-compose up -d auth-service document-service indexing-service quiz-service notification-service

# Wait for core services to be healthy
echo "⏳ Waiting for core services to be healthy..."
sleep 30

# Start the workers
echo "🚀 Starting Celery workers..."
docker-compose up -d document-worker indexing-worker quiz-worker

# Wait for workers to be healthy
echo "⏳ Waiting for workers to be healthy..."
sleep 20

# Start the remaining services
echo "🚀 Starting remaining services..."
docker-compose up -d clarifier-svc question-budget-svc api-gateway web

# Start DLQ services
echo "🚀 Starting DLQ services..."
docker-compose up -d dlq-monitor dlq-api

# Final status check
echo "🔍 Checking service status..."
sleep 10

echo "📊 Service Status:"
docker-compose ps

echo ""
echo "🎉 Study AI Platform is starting up!"
echo "📱 Web UI: http://localhost:3001"
echo "🔌 API Gateway: http://localhost:8000"
echo "📚 Auth Service: http://localhost:8001"
echo "📄 Document Service: http://localhost:8002"
echo "🔍 Indexing Service: http://localhost:8003"
echo "❓ Quiz Service: http://localhost:8004"
echo "🔔 Notification Service: http://localhost:8005"
echo "💬 Clarifier Service: http://localhost:8010"
echo "💰 Question Budget Service: http://localhost:8007"
echo ""
echo "📋 To view logs: docker-compose logs -f [service-name]"
echo "🛑 To stop: docker-compose down"
echo "🔄 To restart: docker-compose restart"
