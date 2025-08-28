#!/bin/bash

# Test Quiz Generation Endpoint
# This script tests if the quiz generation API is working

echo "🧪 Testing Quiz Generation Endpoint"
echo "==================================="

# Check if services are running
echo "📋 Checking service status..."
docker-compose ps | grep -E "(quiz-service|api-gateway)"

echo ""
echo "🔍 Testing quiz generation endpoint..."

# Test the quiz generation endpoint directly
curl -X POST "http://localhost:8000/api/quizzes/generate" \
  -H "Content-Type: application/json" \
  -d '{
    "docIds": ["test-doc-1"],
    "numQuestions": 5,
    "questionTypes": ["MCQ"],
    "difficulty": "medium",
    "language": "auto"
  }' \
  -v

echo ""
echo "🔍 Testing quiz generation endpoint via quiz service directly..."

# Test the quiz service directly
curl -X POST "http://localhost:8004/quizzes/generate" \
  -H "Content-Type: application/json" \
  -d '{
    "docIds": ["test-doc-1"],
    "numQuestions": 5,
    "questionTypes": ["MCQ"],
    "difficulty": "medium",
    "language": "auto"
  }' \
  -v

echo ""
echo "🔍 Testing quiz generation endpoint via quiz service directly (real AI)..."

# Test the real AI quiz generation endpoint
curl -X POST "http://localhost:8004/quizzes/generate-real" \
  -H "Content-Type: application/json" \
  -d '{
    "docIds": ["test-doc-1"],
    "numQuestions": 5,
    "questionTypes": ["MCQ"],
    "difficulty": "medium",
    "language": "auto"
  }' \
  -v

echo ""
echo "🎯 Test completed!"
echo ""
echo "If you see successful responses, the backend is working."
echo "If you see errors, check the service logs:"
echo "docker-compose logs quiz-service"
echo "docker-compose logs api-gateway"
