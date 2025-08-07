#!/bin/bash

# Test Async Quiz Generation Workflow
echo "=== Testing Async Quiz Generation ==="

# Get auth token
echo "1. Getting authentication token..."
TOKEN_RESPONSE=$(curl -s -X POST "http://localhost:8001/login" \
  -H "Content-Type: application/json" \
  -d '{"email": "test@test.com", "password": "test123"}')

TOKEN=$(echo $TOKEN_RESPONSE | jq -r '.access_token')
echo "Token obtained: ${TOKEN:0:50}..."

# Generate quiz (should return immediately)
echo "2. Generating quiz (async)..."
QUIZ_RESPONSE=$(curl -s -X POST "http://localhost:8004/generate/selected-documents" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"topic": "Tay Son Rebellion", "difficulty": "medium", "num_questions": 3, "document_ids": ["0de6d545-8c2b-45f3-a486-f31422d0b2f0"]}')

QUIZ_ID=$(echo $QUIZ_RESPONSE | jq -r '.quiz_id')
STATUS=$(echo $QUIZ_RESPONSE | jq -r '.status')
echo "Quiz ID: $QUIZ_ID"
echo "Initial Status: $STATUS"
echo "Response time: $(echo $QUIZ_RESPONSE | jq -r '.generation_time') seconds"

# Check status immediately
echo "3. Checking status immediately..."
IMMEDIATE_STATUS=$(curl -s -X GET "http://localhost:8004/quizzes/$QUIZ_ID" \
  -H "Authorization: Bearer $TOKEN" | jq -r '.status')
echo "Immediate Status: $IMMEDIATE_STATUS"

# Wait and check status
echo "4. Waiting 30 seconds and checking status..."
sleep 30
STATUS_30S=$(curl -s -X GET "http://localhost:8004/quizzes/$QUIZ_ID" \
  -H "Authorization: Bearer $TOKEN" | jq -r '.status')
echo "Status after 30s: $STATUS_30S"

# Wait more and check again
echo "5. Waiting 60 more seconds and checking status..."
sleep 60
STATUS_90S=$(curl -s -X GET "http://localhost:8004/quizzes/$QUIZ_ID" \
  -H "Authorization: Bearer $TOKEN" | jq -r '.status')
echo "Status after 90s: $STATUS_90S"

# Get final quiz details
echo "6. Getting final quiz details..."
FINAL_QUIZ=$(curl -s -X GET "http://localhost:8004/quizzes/$QUIZ_ID" \
  -H "Authorization: Bearer $TOKEN")

echo "Final Status: $(echo $FINAL_QUIZ | jq -r '.status')"
echo "Final Title: $(echo $FINAL_QUIZ | jq -r '.title')"
echo "Questions Count: $(echo $FINAL_QUIZ | jq -r '.questions | length')"

if [ "$(echo $FINAL_QUIZ | jq -r '.status')" = "completed" ]; then
    echo "✅ Quiz generation completed successfully!"
    echo "Questions:"
    echo $FINAL_QUIZ | jq -r '.questions[] | "  - \(.question)"'
elif [ "$(echo $FINAL_QUIZ | jq -r '.status')" = "failed" ]; then
    echo "❌ Quiz generation failed!"
    echo "Error: $(echo $FINAL_QUIZ | jq -r '.questions.error')"
else
    echo "⏳ Quiz is still processing..."
fi

echo "=== Test Complete ===" 