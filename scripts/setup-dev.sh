#!/bin/bash

# Development Setup Script for Study AI
# This script sets up the local development environment with MinIO and Ollama

set -e

echo "🚀 Study AI - Development Environment Setup"
echo "==========================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

print_header() {
    echo -e "${BLUE}[HEADER]${NC} $1"
}

# Check if we're in the right directory
if [ ! -f "docker-compose.dev.yml" ]; then
    print_error "Please run this script from the study-ai root directory"
    exit 1
fi

print_header "Starting development environment setup..."

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    print_error "Docker is not running. Please start Docker first."
    exit 1
fi

print_header "Starting all services with docker-compose.dev.yml..."

# Start all services
docker-compose -f docker-compose.dev.yml up -d

print_status "Waiting for services to be ready..."
sleep 30

print_header "Setting up MinIO..."

# Wait for MinIO to be ready
print_status "Waiting for MinIO to be ready..."
until docker exec study-ai-minio-dev mc admin info local > /dev/null 2>&1; do
    sleep 5
done

# Create bucket if it doesn't exist
print_status "Creating MinIO bucket..."
docker exec study-ai-minio-dev mc mb local/study-ai-documents --ignore-existing

print_status "MinIO setup completed!"
echo "   MinIO Console: http://localhost:9001"
echo "   Username: minioadmin"
echo "   Password: minioadmin"

print_header "Setting up Ollama..."

# Wait for Ollama to be ready
print_status "Waiting for Ollama to be ready..."
until curl -s http://localhost:11434/api/tags > /dev/null 2>&1; do
    sleep 5
done

# Pull the default model
print_status "Pulling Llama2 model (this may take a while)..."
curl -X POST http://localhost:11434/api/pull -d '{"name": "llama2"}'

print_status "Ollama setup completed!"
echo "   Ollama API: http://localhost:11434"

print_header "Setting up test data..."

# Run the data seeding script
if [ -f "scripts/seed_data_docker.sh" ]; then
    print_status "Creating test users..."
    ./scripts/seed_data_docker.sh
else
    print_warning "Data seeding script not found. You may need to create test users manually."
fi

print_header "Development Environment Summary"
echo "====================================="
echo ""
echo "✅ All services are running:"
echo "   - API Gateway: http://localhost:8000"
echo "   - Auth Service: http://localhost:8001/docs"
echo "   - Document Service: http://localhost:8002/docs"
echo "   - Indexing Service: http://localhost:8003/docs"
echo "   - Quiz Service: http://localhost:8004/docs"
echo "   - Notification Service: http://localhost:8005/docs"
echo "   - Web Frontend: http://localhost:3001"
echo ""
echo "🔧 Development Tools:"
echo "   - MinIO Console: http://localhost:9001 (minioadmin/minioadmin)"
echo "   - Ollama API: http://localhost:11434"
echo ""
echo "🔑 Test Credentials:"
echo "   - Email: test@test.com"
echo "   - Password: test123"
echo ""
echo "📡 WebSocket Endpoints:"
echo "   - Notifications: ws://localhost:8000/ws/{user_id}"
echo ""
echo "🚀 Quick Test Commands:"
echo "   # Test login:"
echo "   curl -X POST http://localhost:8000/auth/login \\"
echo "     -H 'Content-Type: application/json' \\"
echo "     -d '{\"email\": \"test@test.com\", \"password\": \"test123\"}'"
echo ""
echo "   # Test Ollama:"
echo "   curl -X POST http://localhost:11434/api/generate \\"
echo "     -H 'Content-Type: application/json' \\"
echo "     -d '{\"model\": \"llama2\", \"prompt\": \"Hello, how are you?\"}'"
echo ""

print_status "Development environment setup completed successfully!"
print_status "You can now start developing your application!" 