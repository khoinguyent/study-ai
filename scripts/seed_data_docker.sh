#!/bin/bash

# Docker-based Test Data Seeding Script for Study AI
# This script runs the seeding inside the auth service container

set -e

echo "🐳 Study AI - Docker Test Data Seeding Script"
echo "============================================="

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
if [ ! -f "docker-compose.yml" ]; then
    print_error "Please run this script from the study-ai root directory"
    exit 1
fi

print_header "Checking Docker services..."

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    print_error "Docker is not running. Please start Docker first."
    exit 1
fi

# Check if auth service container exists
if ! docker ps -a | grep -q "study-ai-auth-service"; then
    print_warning "Auth service container not found. Starting services..."
    docker-compose up -d auth-service auth-db redis
    print_status "Waiting for services to be ready..."
    sleep 15
fi

# Check if auth service is running
if ! docker ps | grep -q "study-ai-auth-service"; then
    print_warning "Auth service is not running. Starting it..."
    docker-compose up -d auth-service
    print_status "Waiting for service to be ready..."
    sleep 10
fi

print_header "Running data seeding inside Docker container..."

# Copy the seeding script to the container and run it
print_status "Copying seeding script to container..."
docker cp services/auth-service/scripts/seed_data.py study-ai-auth-service:/app/seed_data.py

print_status "Executing seeding script in container..."
docker exec study-ai-auth-service python /app/seed_data.py

print_header "Test Data Summary"
echo "===================="
echo ""
echo "✅ Test users have been created with the following credentials:"
echo ""
echo "🔑 Primary Test User:"
echo "   Email: test@test.com"
echo "   Password: test123"
echo "   Username: testuser"
echo ""
echo "🔑 Additional Test Users:"
echo "   Email: admin@study-ai.com | Password: admin123"
echo "   Email: student@study-ai.com | Password: student123"
echo "   Email: teacher@study-ai.com | Password: teacher123"
echo "   Email: demo@study-ai.com | Password: demo123"
echo ""
echo "🌐 You can now test the application:"
echo "   - Auth Service API: http://localhost:8001/docs"
echo "   - API Gateway: http://localhost"
echo "   - Web Frontend: http://localhost:3001"
echo ""
echo "🚀 Quick Test Commands:"
echo "   # Test login with curl:"
echo "   curl -X POST http://localhost:8001/login \\"
echo "     -H 'Content-Type: application/json' \\"
echo "     -d '{\"email\": \"test@test.com\", \"password\": \"test123\"}'"
echo ""
echo "   # Test through API Gateway:"
echo "   curl -X POST http://localhost/auth/login \\"
echo "     -H 'Content-Type: application/json' \\"
echo "     -d '{\"email\": \"test@test.com\", \"password\": \"test123\"}'"
echo ""

print_status "Docker-based test data seeding completed successfully!" 