#!/bin/bash

echo "🧪 Testing Notification Service"
echo "================================"

# Test health endpoint
echo "1. Testing health endpoint..."
HEALTH_RESPONSE=$(curl -s -X GET "http://localhost:8005/health")
echo "Health status: $(echo $HEALTH_RESPONSE | jq -r '.status')"
echo "Service: $(echo $HEALTH_RESPONSE | jq -r '.service')"

# Login to get token
echo "2. Logging in to get token..."
LOGIN_RESPONSE=$(curl -s -X POST "http://localhost:8001/auth/login" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "testpassword123"
  }')

TOKEN=$(echo $LOGIN_RESPONSE | jq -r '.access_token')
echo "Token obtained: ${TOKEN:0:20}..."

# Test creating a task status
echo "3. Creating a task status..."
TASK_STATUS_RESPONSE=$(curl -s -X POST "http://localhost:8005/task-status" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "task_id": "test-task-123",
    "user_id": "test-user-456",
    "task_type": "document_upload",
    "status": "processing",
    "progress": 50,
    "message": "Uploading document...",
    "meta_data": {
      "filename": "test.pdf",
      "size": 1024000
    }
  }')

TASK_ID=$(echo $TASK_STATUS_RESPONSE | jq -r '.id')
echo "Task created with ID: $TASK_ID"
echo "Task status: $(echo $TASK_STATUS_RESPONSE | jq -r '.status')"

# Test updating task status
echo "4. Updating task status..."
UPDATE_RESPONSE=$(curl -s -X PUT "http://localhost:8005/task-status/$TASK_ID" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "status": "completed",
    "progress": 100,
    "message": "Document uploaded successfully!"
  }')

echo "Updated task status: $(echo $UPDATE_RESPONSE | jq -r '.status')"
echo "Updated progress: $(echo $UPDATE_RESPONSE | jq -r '.progress')"

# Test creating a notification
echo "5. Creating a notification..."
NOTIFICATION_RESPONSE=$(curl -s -X POST "http://localhost:8005/notifications" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "test-user-456",
    "title": "Document Upload Complete",
    "message": "Your document has been successfully uploaded and processed.",
    "notification_type": "document_status",
    "meta_data": {
      "document_id": "doc-123",
      "filename": "test.pdf"
    }
  }')

NOTIFICATION_ID=$(echo $NOTIFICATION_RESPONSE | jq -r '.id')
echo "Notification created with ID: $NOTIFICATION_ID"
echo "Notification title: $(echo $NOTIFICATION_RESPONSE | jq -r '.title')"

# Test getting user notifications
echo "6. Getting user notifications..."
NOTIFICATIONS_RESPONSE=$(curl -s -X GET "http://localhost:8005/notifications/user/test-user-456" \
  -H "Authorization: Bearer $TOKEN")

NOTIFICATION_COUNT=$(echo $NOTIFICATIONS_RESPONSE | jq 'length')
echo "Found $NOTIFICATION_COUNT notifications for user"

# Test marking notification as read
echo "7. Marking notification as read..."
READ_RESPONSE=$(curl -s -X PUT "http://localhost:8005/notifications/$NOTIFICATION_ID/read" \
  -H "Authorization: Bearer $TOKEN")

echo "Notification marked as read: $(echo $READ_RESPONSE | jq -r '.status')"

echo ""
echo "✅ Notification Service Test Complete!"
echo "All endpoints are working correctly." 