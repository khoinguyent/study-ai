#!/bin/bash

# Test script for multipart upload endpoint
# This script tests the /api/documents/upload-multiple endpoint

set -e

# Configuration
API_BASE_URL="http://localhost:8000"
AUTH_TOKEN="your_auth_token_here"  # Replace with actual token
SUBJECT_ID="test-subject-id"        # Replace with actual subject ID
CATEGORY_ID="test-category-id"      # Replace with actual category ID

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${YELLOW}Testing multipart upload endpoint...${NC}"

# Test 1: Valid multipart upload
echo -e "\n${YELLOW}Test 1: Valid multipart upload${NC}"
echo "Creating test files..."

# Create test files
echo "Test content 1" > test_file1.txt
echo "Test content 2" > test_file2.txt

# Test the upload endpoint
echo "Testing upload endpoint..."
response=$(curl -s -w "\n%{http_code}" \
  -X POST \
  -H "Authorization: Bearer $AUTH_TOKEN" \
  -F "files=@test_file1.txt" \
  -F "files=@test_file2.txt" \
  -F "subject_id=$SUBJECT_ID" \
  -F "category_id=$CATEGORY_ID" \
  "$API_BASE_URL/api/documents/upload-multiple")

# Extract status code and response body
http_code=$(echo "$response" | tail -n1)
response_body=$(echo "$response" | head -n -1)

echo "HTTP Status: $http_code"
echo "Response: $response_body"

if [ "$http_code" -eq 200 ]; then
    echo -e "${GREEN}✓ Test 1 passed: Valid upload succeeded${NC}"
else
    echo -e "${RED}✗ Test 1 failed: Expected 200, got $http_code${NC}"
fi

# Test 2: Missing subject_id (should return 422)
echo -e "\n${YELLOW}Test 2: Missing subject_id (should return 422)${NC}"
response=$(curl -s -w "\n%{http_code}" \
  -X POST \
  -H "Authorization: Bearer $AUTH_TOKEN" \
  -F "files=@test_file1.txt" \
  -F "category_id=$CATEGORY_ID" \
  "$API_BASE_URL/api/documents/upload-multiple")

http_code=$(echo "$response" | tail -n1)
response_body=$(echo "$response" | head -n -1)

echo "HTTP Status: $http_code"
echo "Response: $response_body"

if [ "$http_code" -eq 422 ]; then
    echo -e "${GREEN}✓ Test 2 passed: Missing subject_id correctly returned 422${NC}"
else
    echo -e "${RED}✗ Test 2 failed: Expected 422, got $http_code${NC}"
fi

# Test 3: No files (should return 422)
echo -e "\n${YELLOW}Test 3: No files (should return 422)${NC}"
response=$(curl -s -w "\n%{http_code}" \
  -X POST \
  -H "Authorization: Bearer $AUTH_TOKEN" \
  -F "subject_id=$SUBJECT_ID" \
  -F "category_id=$CATEGORY_ID" \
  "$API_BASE_URL/api/documents/upload-multiple")

http_code=$(echo "$response" | tail -n1)
response_body=$(echo "$response" | head -n -1)

echo "HTTP Status: $http_code"
echo "Response: $response_body"

if [ "$http_code" -eq 422 ]; then
    echo -e "${GREEN}✓ Test 3 passed: No files correctly returned 422${NC}"
else
    echo -e "${RED}✗ Test 3 failed: Expected 422, got $http_code${NC}"
fi

# Test 4: Test camelCase field names (should work as aliases)
echo -e "\n${YELLOW}Test 4: camelCase field names (should work as aliases)${NC}"
response=$(curl -s -w "\n%{http_code}" \
  -X POST \
  -H "Authorization: Bearer $AUTH_TOKEN" \
  -F "files=@test_file1.txt" \
  -F "subjectId=$SUBJECT_ID" \
  -F "categoryId=$CATEGORY_ID" \
  "$API_BASE_URL/api/documents/upload-multiple")

http_code=$(echo "$response" | tail -n1)
response_body=$(echo "$response" | head -n -1)

echo "HTTP Status: $http_code"
echo "Response: $response_body"

if [ "$http_code" -eq 200 ]; then
    echo -e "${GREEN}✓ Test 4 passed: camelCase field names worked as aliases${NC}"
else
    echo -e "${RED}✗ Test 4 failed: Expected 200, got $http_code${NC}"
fi

# Cleanup
echo -e "\n${YELLOW}Cleaning up test files...${NC}"
rm -f test_file1.txt test_file2.txt

echo -e "\n${GREEN}All tests completed!${NC}"
