#!/bin/bash

# Postman Collection Validation Script
# This script validates the Postman collection and tests basic connectivity

set -e

echo "🧪 Study AI - Postman Collection Validation"
echo "=========================================="

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

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_header() {
    echo -e "${BLUE}[HEADER]${NC} $1"
}

# Check if we're in the right directory
if [ ! -f "postman/Study-AI-API-Collection.json" ]; then
    print_error "Postman collection not found. Please run this script from the study-ai root directory."
    exit 1
fi

print_header "Validating Postman Collection..."

# Check if jq is available for JSON validation
if command -v jq &> /dev/null; then
    print_status "Validating JSON format..."
    if jq empty postman/Study-AI-API-Collection.json 2>/dev/null; then
        print_success "✅ Postman collection JSON is valid"
    else
        print_error "❌ Postman collection JSON is invalid"
        exit 1
    fi
    
    # Count endpoints
    endpoint_count=$(jq '.item[].item | length' postman/Study-AI-API-Collection.json | awk '{sum += $1} END {print sum}')
    print_status "Found $endpoint_count API endpoints in collection"
else
    print_warning "jq not found. Skipping JSON validation."
fi

print_header "Testing Basic Connectivity..."

# Test API Gateway health
print_status "Testing API Gateway..."
if curl -s http://localhost:8000/health > /dev/null; then
    print_success "✅ API Gateway is accessible"
else
    print_error "❌ API Gateway is not accessible"
    print_warning "Make sure your development environment is running:"
    print_warning "  ./scripts/setup-dev.sh"
    exit 1
fi

# Test individual services
services=(
    "auth:8001"
    "documents:8002"
    "indexing:8003"
    "quizzes:8004"
    "notifications:8005"
)

for service in "${services[@]}"; do
    service_name=$(echo $service | cut -d: -f1)
    service_port=$(echo $service | cut -d: -f2)
    
    print_status "Testing $service_name service..."
    if curl -s http://localhost:$service_port/health > /dev/null; then
        print_success "✅ $service_name service is accessible"
    else
        print_warning "⚠️  $service_name service is not accessible"
    fi
done

# Test development tools
print_header "Testing Development Tools..."

# Test MinIO
print_status "Testing MinIO..."
if curl -s http://localhost:9001 > /dev/null; then
    print_success "✅ MinIO console is accessible"
else
    print_warning "⚠️  MinIO console is not accessible"
fi

# Test Ollama
print_status "Testing Ollama..."
if curl -s http://localhost:11434/api/tags > /dev/null; then
    print_success "✅ Ollama API is accessible"
else
    print_warning "⚠️  Ollama API is not accessible"
fi

print_header "Postman Collection Summary"
echo "==============================="
echo ""
echo "📁 Collection Files:"
echo "   ✅ Study-AI-API-Collection.json"
echo "   ✅ Study-AI-Environment.json"
echo "   ✅ README.md"
echo ""
echo "🔗 Import Instructions:"
echo "   1. Open Postman"
echo "   2. Import Study-AI-API-Collection.json"
echo "   3. Import Study-AI-Environment.json"
echo "   4. Select 'Study AI - Development Environment'"
echo "   5. Start testing with 'Login User' endpoint"
echo ""
echo "🌐 Service Endpoints:"
echo "   - API Gateway: http://localhost:8000"
echo "   - Auth Service: http://localhost:8001"
echo "   - Document Service: http://localhost:8002"
echo "   - Indexing Service: http://localhost:8003"
echo "   - Quiz Service: http://localhost:8004"
echo "   - Notification Service: http://localhost:8005"
echo ""
echo "🔑 Test Credentials:"
echo "   - Email: test@test.com"
echo "   - Password: test123"
echo ""
echo "📖 Documentation:"
echo "   - See postman/README.md for detailed usage instructions"
echo ""

print_success "Postman collection validation completed!"
print_status "You can now import the collection and start testing your APIs!" 