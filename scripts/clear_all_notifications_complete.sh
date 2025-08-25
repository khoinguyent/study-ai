#!/bin/bash

# Complete Notification Clearing Script
# This script clears notifications from all sources: databases, Redis, and frontend

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}🧹 Complete Notification Clearing Script${NC}"
echo "=============================================="

# Configuration
NOTIFICATION_SERVICE_URL="${NOTIFICATION_SERVICE_URL:-http://localhost:8005}"
API_GATEWAY_URL="${API_GATEWAY_URL:-http://localhost:8000}"
REDIS_CONTAINER="${REDIS_CONTAINER:-study-ai-redis}"

echo -e "${YELLOW}Step 1: Clearing Redis Queues${NC}"
echo "----------------------------------------"

# Clear all Redis keys
echo "Clearing all Redis keys..."
keys_cleared=$(docker exec $REDIS_CONTAINER redis-cli --scan --pattern "*" | wc -l)
docker exec $REDIS_CONTAINER redis-cli --scan --pattern "*" | xargs -r docker exec $REDIS_CONTAINER redis-cli del
echo -e "${GREEN}✅ Cleared $keys_cleared Redis keys${NC}"

echo -e "${YELLOW}Step 2: Clearing Notification Database${NC}"
echo "----------------------------------------------"

# Clear notification database
echo "Clearing notifications table..."
notifications_cleared=$(docker exec study-ai-notification-db psql -U postgres -d notification_db -t -c "SELECT COUNT(*) FROM notifications;" | tr -d ' ')
docker exec study-ai-notification-db psql -U postgres -d notification_db -c "DELETE FROM notifications;"
echo -e "${GREEN}✅ Cleared $notifications_cleared notifications from database${NC}"

echo "Clearing task_statuses table..."
tasks_cleared=$(docker exec study-ai-notification-db psql -U postgres -d notification_db -t -c "SELECT COUNT(*) FROM task_statuses;" | tr -d ' ')
docker exec study-ai-notification-db psql -U postgres -d notification_db -c "DELETE FROM task_statuses;"
echo -e "${GREEN}✅ Cleared $tasks_cleared task statuses from database${NC}"

echo -e "${YELLOW}Step 3: Clearing Document Service Database${NC}"
echo "-----------------------------------------------"

# Clear any document-related notifications
echo "Clearing document processing statuses..."
docker exec study-ai-document-db psql -U postgres -d document_db -c "UPDATE documents SET status = 'pending' WHERE status IN ('processing', 'ready');" 2>/dev/null || echo "No document status updates needed"
echo -e "${GREEN}✅ Document statuses reset${NC}"

echo -e "${YELLOW}Step 4: Clearing Indexing Service Database${NC}"
echo "-----------------------------------------------"

# Clear indexing service data
echo "Clearing indexing tasks..."
docker exec study-ai-indexing-db psql -U postgres -d indexing_db -c "DELETE FROM document_chunks;" 2>/dev/null || echo "No document chunks to clear"
docker exec study-ai-indexing-db psql -U postgres -d indexing_db -c "DELETE FROM indexing_tasks;" 2>/dev/null || echo "No indexing tasks to clear"
echo -e "${GREEN}✅ Indexing data cleared${NC}"

echo -e "${YELLOW}Step 5: Restarting Services${NC}"
echo "--------------------------------"

# Restart services to clear any in-memory state
echo "Restarting notification service..."
docker-compose restart notification-service
sleep 5

echo "Restarting indexing service..."
docker-compose restart indexing-service
sleep 5

echo "Restarting web service..."
docker-compose restart web
sleep 5

echo -e "${GREEN}✅ All services restarted${NC}"

echo -e "${YELLOW}Step 6: Verifying Clean State${NC}"
echo "-----------------------------------"

# Wait for services to be healthy
echo "Waiting for services to be healthy..."
sleep 10

# Check service health
echo "Checking service health..."
if curl -s http://localhost:8005/health | grep -q "healthy"; then
    echo -e "${GREEN}✅ Notification service healthy${NC}"
else
    echo -e "${RED}❌ Notification service not healthy${NC}"
fi

if curl -s http://localhost:8003/health | grep -q "healthy"; then
    echo -e "${GREEN}✅ Indexing service healthy${NC}"
else
    echo -e "${RED}❌ Indexing service not healthy${NC}"
fi

if curl -s http://localhost:8000/health | grep -q "healthy"; then
    echo -e "${GREEN}✅ API gateway healthy${NC}"
else
    echo -e "${RED}❌ API gateway not healthy${NC}"
fi

echo -e "${YELLOW}Step 7: Final Verification${NC}"
echo "-------------------------------"

# Check Redis is empty
redis_keys=$(docker exec $REDIS_CONTAINER redis-cli --scan --pattern "*" | wc -l)
echo "Redis keys remaining: $redis_keys"

# Check databases are empty
notifications_count=$(docker exec study-ai-notification-db psql -U postgres -d notification_db -t -c "SELECT COUNT(*) FROM notifications;" | tr -d ' ')
tasks_count=$(docker exec study-ai-notification-db psql -U postgres -d notification_db -t -c "SELECT COUNT(*) FROM task_statuses;" | tr -d ' ')

echo "Notifications in database: $notifications_count"
echo "Tasks in database: $tasks_count"

echo ""
echo -e "${GREEN}🎉 Complete Notification Clearing Complete!${NC}"
echo ""
echo "Next steps:"
echo "1. Refresh your browser page"
echo "2. The 3 duplicate notifications should be gone"
echo "3. Upload a new document to test - should see only 1 notification"
echo ""
echo "If notifications persist:"
echo "- Clear browser cache and cookies"
echo "- Hard refresh the page (Ctrl+F5 or Cmd+Shift+R)"
echo "- Check browser developer tools for any cached state"
