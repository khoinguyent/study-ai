#!/bin/bash

# Test script for the clarification flow
# This script tests the new study session endpoints

set -e

echo "🧪 Testing Clarification Flow"
echo "=============================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
API_BASE="http://localhost:8000"
CLARIFIER_BASE="http://localhost:8010"
BUDGET_BASE="http://localhost:8011"

# Test data
SESSION_ID="test_session_$(date +%s)"
USER_ID="test_user_123"
SUBJECT_ID="history_101"
DOC_IDS='["doc1", "doc2", "doc3"]'

echo -e "${BLUE}Test Configuration:${NC}"
echo "  API Gateway: $API_BASE"
echo "  Clarifier Service: $CLARIFIER_BASE"
echo "  Budget Service: $BUDGET_BASE"
echo "  Session ID: $SESSION_ID"
echo ""

# Function to check service health
check_health() {
    local service_name=$1
    local url=$2
    
    echo -e "${YELLOW}Checking $service_name health...${NC}"
    if curl -s "$url/health" > /dev/null; then
        echo -e "  ${GREEN}✅ $service_name is healthy${NC}"
        return 0
    else
        echo -e "  ${RED}❌ $service_name is not responding${NC}"
        return 1
    fi
}

# Function to test endpoint
test_endpoint() {
    local name=$1
    local method=$2
    local url=$3
    local data=$4
    
    echo -e "${YELLOW}Testing $name...${NC}"
    echo "  $method $url"
    
    if [ -n "$data" ]; then
        echo "  Data: $data"
    fi
    
    if [ "$method" = "GET" ]; then
        response=$(curl -s -w "\n%{http_code}" "$url")
    else
        response=$(curl -s -w "\n%{http_code}" -X "$method" -H "Content-Type: application/json" -d "$data" "$url")
    fi
    
    http_code=$(echo "$response" | tail -n1)
    body=$(echo "$response" | head -n -1)
    
    if [ "$http_code" -ge 200 ] && [ "$http_code" -lt 300 ]; then
        echo -e "  ${GREEN}✅ Success (HTTP $http_code)${NC}"
        echo "  Response: $body" | jq . 2>/dev/null || echo "  Response: $body"
    else
        echo -e "  ${RED}❌ Failed (HTTP $http_code)${NC}"
        echo "  Response: $body"
    fi
    
    echo ""
}

# Check all services are healthy
echo -e "${BLUE}Health Checks${NC}"
echo "============="

check_health "API Gateway" "$API_BASE" || exit 1
check_health "Clarifier Service" "$CLARIFIER_BASE" || exit 1
check_health "Budget Service" "$BUDGET_BASE" || exit 1

echo ""

# Test budget service directly
echo -e "${BLUE}Testing Budget Service Directly${NC}"
echo "====================================="

budget_data='{"docIds": ["doc1", "doc2", "doc3"], "difficulty": "mixed"}'
test_endpoint "Budget Calculation" "POST" "$BUDGET_BASE/budget" "$budget_data"

# Test clarifier service directly
echo -e "${BLUE}Testing Clarifier Service Directly${NC}"
echo "=========================================="

start_data="{\"sessionId\": \"$SESSION_ID\", \"userId\": \"$USER_ID\", \"subjectId\": \"$SUBJECT_ID\", \"docIds\": $DOC_IDS}"
test_endpoint "Clarification Start" "POST" "$CLARIFIER_BASE/clarifier/start" "$start_data"

confirm_data="{\"sessionId\": \"$SESSION_ID\", \"userId\": \"$USER_ID\", \"subjectId\": \"$SUBJECT_ID\", \"docIds\": $DOC_IDS, \"question_types\": [\"mcq\", \"true_false\"], \"difficulty\": \"mixed\", \"requested_count\": 12}"
test_endpoint "Clarification Confirm" "POST" "$CLARIFIER_BASE/clarifier/confirm" "$confirm_data"

# Test through API Gateway
echo -e "${BLUE}Testing Through API Gateway${NC}"
echo "================================="

test_endpoint "Study Session Start (Gateway)" "POST" "$API_BASE/study-sessions/start" "$start_data"
test_endpoint "Study Session Confirm (Gateway)" "POST" "$API_BASE/study-sessions/confirm" "$confirm_data"

echo -e "${GREEN}🎉 All tests completed!${NC}"
echo ""
echo -e "${BLUE}Test Summary:${NC}"
echo "  - Budget Service: Direct endpoint tested"
echo "  - Clarifier Service: Direct endpoints tested"
echo "  - API Gateway: Proxied endpoints tested"
echo "  - Session ID used: $SESSION_ID"
echo ""
echo -e "${YELLOW}Note:${NC} These tests use placeholder data. In a real scenario, you would:"
echo "  1. Use real document IDs from your document service"
echo "  2. Include proper authentication headers"
echo "  3. Validate the quiz generation was triggered"
echo "  4. Check the quiz service received the generation request"

