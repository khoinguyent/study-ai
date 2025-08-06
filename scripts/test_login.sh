#!/bin/bash

# Test Login Script for Study AI
# This script tests the login functionality with the test user

set -e

echo "🧪 Study AI - Login Test Script"
echo "==============================="

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

# Test credentials
TEST_EMAIL="test@test.com"
TEST_PASSWORD="test123"

print_header "Testing login functionality..."

# Test 1: Direct Auth Service Login
print_status "Testing direct Auth Service login..."
AUTH_RESPONSE=$(curl -s -X POST http://localhost:8001/login \
  -H 'Content-Type: application/json' \
  -d "{\"email\": \"$TEST_EMAIL\", \"password\": \"$TEST_PASSWORD\"}")

if echo "$AUTH_RESPONSE" | grep -q "access_token"; then
    print_success "✅ Direct Auth Service login successful!"
    AUTH_TOKEN=$(echo "$AUTH_RESPONSE" | grep -o '"access_token":"[^"]*"' | cut -d'"' -f4)
    echo "   Token: ${AUTH_TOKEN:0:20}..."
else
    print_error "❌ Direct Auth Service login failed!"
    echo "   Response: $AUTH_RESPONSE"
fi

# Test 2: API Gateway Login
print_status "Testing API Gateway login..."
GATEWAY_RESPONSE=$(curl -s -X POST http://localhost:8000/auth/login \
  -H 'Content-Type: application/json' \
  -d "{\"email\": \"$TEST_EMAIL\", \"password\": \"$TEST_PASSWORD\"}")

if echo "$GATEWAY_RESPONSE" | grep -q "access_token"; then
    print_success "✅ API Gateway login successful!"
    GATEWAY_TOKEN=$(echo "$GATEWAY_RESPONSE" | grep -o '"access_token":"[^"]*"' | cut -d'"' -f4)
    echo "   Token: ${GATEWAY_TOKEN:0:20}..."
else
    print_error "❌ API Gateway login failed!"
    echo "   Response: $GATEWAY_RESPONSE"
fi

# Test 3: Token Verification
if [ ! -z "$AUTH_TOKEN" ]; then
    print_status "Testing token verification..."
    VERIFY_RESPONSE=$(curl -s -X POST http://localhost:8001/verify \
      -H "Authorization: Bearer $AUTH_TOKEN")
    
    if echo "$VERIFY_RESPONSE" | grep -q "valid.*true"; then
        print_success "✅ Token verification successful!"
    else
        print_error "❌ Token verification failed!"
        echo "   Response: $VERIFY_RESPONSE"
    fi
fi

# Test 4: Get User Profile
if [ ! -z "$AUTH_TOKEN" ]; then
    print_status "Testing user profile retrieval..."
    PROFILE_RESPONSE=$(curl -s -X GET http://localhost:8001/me \
      -H "Authorization: Bearer $AUTH_TOKEN")
    
    if echo "$PROFILE_RESPONSE" | grep -q "test@test.com"; then
        print_success "✅ User profile retrieval successful!"
        echo "   User: $(echo "$PROFILE_RESPONSE" | grep -o '"email":"[^"]*"' | cut -d'"' -f4)"
    else
        print_error "❌ User profile retrieval failed!"
        echo "   Response: $PROFILE_RESPONSE"
    fi
fi

print_header "Test Summary"
echo "=============="
echo ""
echo "🔑 Test Credentials Used:"
echo "   Email: $TEST_EMAIL"
echo "   Password: $TEST_PASSWORD"
echo ""
echo "🌐 Test Endpoints:"
echo "   - Auth Service: http://localhost:8001"
echo "   - API Gateway: http://localhost:8000"
echo ""
echo "📋 Test Results:"
if echo "$AUTH_RESPONSE" | grep -q "access_token" && echo "$GATEWAY_RESPONSE" | grep -q "access_token"; then
    print_success "All login tests passed! ✅"
else
    print_warning "Some tests failed. Check the output above. ⚠️"
fi
echo "" 