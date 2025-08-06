#!/bin/bash

# Test script for Study AI API endpoints

echo "🧪 Testing Study AI API endpoints..."

# Base URL
BASE_URL="http://localhost"

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to test endpoint
test_endpoint() {
    local endpoint=$1
    local method=${2:-GET}
    local data=$3
    
    echo -n "Testing $method $endpoint... "
    
    if [ "$method" = "POST" ] && [ -n "$data" ]; then
        response=$(curl -s -w "%{http_code}" -X $method -H "Content-Type: application/json" -d "$data" "$BASE_URL$endpoint")
    else
        response=$(curl -s -w "%{http_code}" -X $method "$BASE_URL$endpoint")
    fi
    
    # Extract status code (last 3 characters)
    status_code=${response: -3}
    # Extract response body (everything except last 3 characters)
    body=${response%???}
    
    if [ "$status_code" = "200" ]; then
        echo -e "${GREEN}✅ OK${NC}"
        echo "   Response: $body"
    else
        echo -e "${RED}❌ Failed (Status: $status_code)${NC}"
        echo "   Response: $body"
    fi
    echo ""
}

# Wait for services to be ready
echo -e "${YELLOW}⏳ Waiting for services to be ready...${NC}"
sleep 5

# Test health endpoints
echo "🏥 Testing health endpoints..."
test_endpoint "/health"
test_endpoint "/api/health"

# Test API endpoints
echo "🔧 Testing API endpoints..."
test_endpoint "/api/chat" "POST" '{"message": "Hello, how are you?"}'

echo "📤 Testing file upload endpoint..."
# Create a test file
echo "This is a test document for upload testing." > test_document.txt

# Test file upload (simplified - just check if endpoint responds)
echo -n "Testing POST /api/upload... "
upload_response=$(curl -s -w "%{http_code}" -X POST -F "file=@test_document.txt" "$BASE_URL/api/upload")
upload_status=${upload_response: -3}
upload_body=${upload_response%???}

if [ "$upload_status" = "200" ]; then
    echo -e "${GREEN}✅ OK${NC}"
    echo "   Response: $upload_body"
else
    echo -e "${RED}❌ Failed (Status: $upload_status)${NC}"
    echo "   Response: $upload_body"
fi

# Clean up test file
rm -f test_document.txt

echo ""
echo -e "${GREEN}🎉 API testing completed!${NC}"
echo ""
echo "📋 Test Summary:"
echo "   - Health endpoints: Should return 200 OK"
echo "   - Chat endpoint: Should accept POST requests"
echo "   - Upload endpoint: Should accept file uploads"
echo ""
echo "💡 If any tests failed, check:"
echo "   1. Docker containers are running: docker-compose ps"
echo "   2. Service logs: docker-compose logs [service-name]"
echo "   3. Environment variables are set correctly" 