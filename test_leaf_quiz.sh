#!/bin/bash

# Test Leaf Quiz Service using T5 Transformers
echo "=== Testing Leaf Quiz Service (T5 Transformers) ==="

# Get auth token
echo "1. Getting authentication token..."
TOKEN_RESPONSE=$(curl -s -X POST "http://localhost:8001/login" \
  -H "Content-Type: application/json" \
  -d '{"email": "test@test.com", "password": "test123"}')

TOKEN=$(echo $TOKEN_RESPONSE | jq -r '.access_token')
echo "Token obtained: ${TOKEN:0:50}..."

# Test health endpoint
echo "2. Testing health endpoint..."
HEALTH_RESPONSE=$(curl -s -X GET "http://localhost:8006/health")
echo "Health status: $(echo $HEALTH_RESPONSE | jq -r '.status')"
echo "Model initialized: $(echo $HEALTH_RESPONSE | jq -r '.model_initialized')"

# Test model endpoint
echo "3. Testing T5 models..."
MODEL_RESPONSE=$(curl -s -X GET "http://localhost:8006/test-models")
echo "Model test status: $(echo $MODEL_RESPONSE | jq -r '.status')"
echo "Message: $(echo $MODEL_RESPONSE | jq -r '.message')"

# Generate quiz from text
echo "4. Generating quiz from text using T5 transformers..."
QUIZ_RESPONSE=$(curl -s -X POST "http://localhost:8006/generate" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "source_text": "The Tay Son Rebellion was a peasant uprising in Vietnam from 1771 to 1802. It was led by three brothers: Nguyen Nhac, Nguyen Hue, and Nguyen Lu. The rebellion began in response to economic hardship and social inequality. Nguyen Hue, also known as Quang Trung, became the most famous leader and briefly unified Vietnam. The rebellion ultimately failed when Nguyen Anh, with French support, defeated the Tay Son forces and established the Nguyen Dynasty.",
    "num_questions": 3,
    "difficulty": "medium",
    "topic": "Tay Son Rebellion History"
  }')

QUIZ_ID=$(echo $QUIZ_RESPONSE | jq -r '.quiz_id')
STATUS=$(echo $QUIZ_RESPONSE | jq -r '.status')
echo "Quiz ID: $QUIZ_ID"
echo "Initial Status: $STATUS"
echo "Response time: $(echo $QUIZ_RESPONSE | jq -r '.generation_time') seconds"

# Check status immediately
echo "5. Checking status immediately..."
IMMEDIATE_STATUS=$(curl -s -X GET "http://localhost:8006/quizzes/$QUIZ_ID" \
  -H "Authorization: Bearer $TOKEN" | jq -r '.status')
echo "Immediate Status: $IMMEDIATE_STATUS"

# Wait and check status
echo "6. Waiting 30 seconds and checking status..."
sleep 30
STATUS_30S=$(curl -s -X GET "http://localhost:8006/quizzes/$QUIZ_ID" \
  -H "Authorization: Bearer $TOKEN" | jq -r '.status')
echo "Status after 30s: $STATUS_30S"

# Wait more and check again
echo "7. Waiting 60 more seconds and checking status..."
sleep 60
STATUS_90S=$(curl -s -X GET "http://localhost:8006/quizzes/$QUIZ_ID" \
  -H "Authorization: Bearer $TOKEN" | jq -r '.status')
echo "Status after 90s: $STATUS_90S"

# Get final quiz details
echo "8. Getting final quiz details..."
FINAL_QUIZ=$(curl -s -X GET "http://localhost:8006/quizzes/$QUIZ_ID" \
  -H "Authorization: Bearer $TOKEN")

echo "Final Status: $(echo $FINAL_QUIZ | jq -r '.status')"
echo "Final Title: $(echo $FINAL_QUIZ | jq -r '.title')"
echo "Questions Count: $(echo $FINAL_QUIZ | jq -r '.questions | length')"
echo "Generation Time: $(echo $FINAL_QUIZ | jq -r '.generation_time') seconds"

if [ "$(echo $FINAL_QUIZ | jq -r '.status')" = "completed" ]; then
    echo "✅ Quiz generation completed successfully!"
    echo "Questions:"
    echo $FINAL_QUIZ | jq -r '.questions[] | "  - \(.question)"'
    echo ""
    echo "Sample question details:"
    echo $FINAL_QUIZ | jq -r '.questions[0] | "Question: \(.question)\nOptions: \(.options)\nCorrect Answer: \(.correct_answer)\nExplanation: \(.explanation)"'
elif [ "$(echo $FINAL_QUIZ | jq -r '.status')" = "failed" ]; then
    echo "❌ Quiz generation failed!"
    echo "Error: $(echo $FINAL_QUIZ | jq -r '.questions.error')"
else
    echo "⏳ Quiz is still processing..."
fi

echo ""
echo "=== Test Complete ===" 