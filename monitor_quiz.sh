#!/bin/bash

# Monitor Quiz Generation for 20 minutes
QUIZ_ID="0fb99153-aaa1-4849-bbc0-bd9780cc8efc"
TOKEN="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJjM2ViMWQwOC1jZWQ1LTQ0OWYtYWQ3ZC1mN2E5ZjBjNWNiODAiLCJleHAiOjE3NTQ1NDQ0ODZ9.90gluCmJcZ65AXPxnQ9ycBlkRWgTUsDkSRnTLiVYTzI"

echo "=== Monitoring Quiz Generation for 20 minutes ==="
echo "Quiz ID: $QUIZ_ID"
echo "Start time: $(date)"
echo ""

# Check initial status
echo "Initial status check:"
curl -s -X GET "http://localhost:8004/quizzes/$QUIZ_ID" \
  -H "Authorization: Bearer $TOKEN" | jq -r '.status'
echo ""

# Monitor every 2 minutes for 20 minutes (10 checks)
for i in {1..10}; do
    echo "Check $i/10 - $(date)"
    STATUS=$(curl -s -X GET "http://localhost:8004/quizzes/$QUIZ_ID" \
      -H "Authorization: Bearer $TOKEN" | jq -r '.status')
    echo "Status: $STATUS"
    
    if [ "$STATUS" = "completed" ]; then
        echo "✅ Quiz generation completed!"
        echo "Final result:"
        curl -s -X GET "http://localhost:8004/quizzes/$QUIZ_ID" \
          -H "Authorization: Bearer $TOKEN" | jq '.'
        break
    elif [ "$STATUS" = "failed" ]; then
        echo "❌ Quiz generation failed!"
        echo "Error details:"
        curl -s -X GET "http://localhost:8004/quizzes/$QUIZ_ID" \
          -H "Authorization: Bearer $TOKEN" | jq '.questions'
        break
    fi
    
    if [ $i -lt 10 ]; then
        echo "Waiting 2 minutes..."
        sleep 120
        echo ""
    fi
done

echo ""
echo "Final status check at $(date):"
FINAL_RESULT=$(curl -s -X GET "http://localhost:8004/quizzes/$QUIZ_ID" \
  -H "Authorization: Bearer $TOKEN")

echo "Status: $(echo $FINAL_RESULT | jq -r '.status')"
echo "Title: $(echo $FINAL_RESULT | jq -r '.title')"

if [ "$(echo $FINAL_RESULT | jq -r '.status')" = "completed" ]; then
    echo "✅ Quiz generation completed successfully!"
    echo "Questions:"
    echo $FINAL_RESULT | jq -r '.questions[] | "  - \(.question)"'
elif [ "$(echo $FINAL_RESULT | jq -r '.status')" = "failed" ]; then
    echo "❌ Quiz generation failed!"
    echo "Error: $(echo $FINAL_RESULT | jq -r '.questions.error')"
else
    echo "⏳ Quiz is still processing..."
fi

echo ""
echo "=== Monitoring Complete ===" 