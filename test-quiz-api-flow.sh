#!/bin/bash

# Test Quiz Generation API Flow
# This script tests the complete flow from login to quiz generation

echo "🧪 Testing Complete Quiz Generation API Flow"
echo "============================================="

# Step 1: Login to get auth token
echo "🔐 Step 1: Logging in to get auth token..."
LOGIN_RESPONSE=$(curl -s -X POST "http://localhost:8000/auth/login" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@test.com",
    "password": "test123"
  }')

echo "Login response: $LOGIN_RESPONSE"

# Extract token (assuming response has a token field)
TOKEN=$(echo $LOGIN_RESPONSE | grep -o '"token":"[^"]*"' | cut -d'"' -f4)

if [ -z "$TOKEN" ]; then
    echo "❌ Failed to get auth token. Trying alternative response format..."
    # Try different response formats
    TOKEN=$(echo $LOGIN_RESPONSE | grep -o '"access_token":"[^"]*"' | cut -d'"' -f4)
fi

if [ -z "$TOKEN" ]; then
    echo "❌ Still no token found. Response was: $LOGIN_RESPONSE"
    echo "Continuing without token for testing..."
    TOKEN=""
else
    echo "✅ Got auth token: ${TOKEN:0:20}..."
fi

# Step 2: Test quiz generation with the token
echo ""
echo "🚀 Step 2: Testing quiz generation with AI (should call OpenAI)..."

if [ -n "$TOKEN" ]; then
    QUIZ_RESPONSE=$(curl -s -X POST "http://localhost:8000/api/quizzes/generate" \
      -H "Content-Type: application/json" \
      -H "Authorization: Bearer $TOKEN" \
      -d '{
        "docIds": ["test-doc-1", "test-doc-2"],
        "numQuestions": 10,
        "questionTypes": ["MCQ", "TRUE_FALSE", "FILL_BLANK"],
        "difficulty": "medium",
        "language": "auto"
      }')
else
    QUIZ_RESPONSE=$(curl -s -X POST "http://localhost:8000/api/quizzes/generate" \
      -H "Content-Type: application/json" \
      -d '{
        "docIds": ["test-doc-1", "test-doc-2"],
        "numQuestions": 10,
        "questionTypes": ["MCQ", "TRUE_FALSE", "FILL_BLANK"],
        "difficulty": "medium",
        "language": "auto"
      }')
fi

echo "Quiz generation response: $QUIZ_RESPONSE"

# Extract job_id from response
JOB_ID=$(echo $QUIZ_RESPONSE | grep -o '"job_id":"[^"]*"' | cut -d'"' -f4)

if [ -n "$JOB_ID" ]; then
    echo "✅ Got job_id: $JOB_ID"
    
    # Step 3: Test events endpoint
    echo ""
    echo "📡 Step 3: Testing quiz events endpoint..."
    
    if [ -n "$TOKEN" ]; then
        EVENTS_RESPONSE=$(curl -s -X GET "http://localhost:8000/api/quizzes/$JOB_ID/events" \
          -H "Authorization: Bearer $TOKEN")
    else
        EVENTS_RESPONSE=$(curl -s -X GET "http://localhost:8000/api/quizzes/$JOB_ID/events")
    fi
    
    echo "Events response: $EVENTS_RESPONSE"
    
    # Check if events endpoint is working
    if echo "$EVENTS_RESPONSE" | grep -q "events"; then
        echo "✅ Events endpoint is working!"
    else
        echo "❌ Events endpoint failed or returned unexpected format"
    fi
else
    echo "❌ No job_id found in response"
fi

echo ""
echo "🎯 Test completed!"
echo ""
echo "Now check the backend logs to see if OpenAI was called:"
echo "docker-compose logs -f quiz-service | grep -E '(generate-real|OpenAI|AI-powered|quiz_real)'"
echo ""
echo "Expected logs:"
echo "🚀 [BACKEND] Real quiz generation request received: quiz_real_..."
echo "🤖 [OPENAI] Starting OpenAI API call: openai_..."
echo "📤 [OPENAI] Sending OpenAI API request: { model: 'gpt-3.5-turbo' }"
echo "✅ [OPENAI] OpenAI API response received: { response_time: 'X.XXs' }"
