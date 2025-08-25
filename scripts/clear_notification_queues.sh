#!/bin/bash

# Clear Notification Queues Script
# This script helps clear pending notifications and notification queues

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
NOTIFICATION_SERVICE_URL="${NOTIFICATION_SERVICE_URL:-http://localhost:8000}"
AUTH_TOKEN="${AUTH_TOKEN:-}"
USER_ID="${USER_ID:-}"

echo -e "${BLUE}🔔 Notification Queue Clearing Script${NC}"
echo "=================================="

# Function to check if service is running
check_service() {
    local service_url=$1
    local service_name=$2
    
    echo -e "${YELLOW}Checking if ${service_name} is running...${NC}"
    
    if curl -s --connect-timeout 5 "${service_url}/health" > /dev/null 2>&1; then
        echo -e "${GREEN}✅ ${service_name} is running${NC}"
        return 0
    else
        echo -e "${RED}❌ ${service_name} is not running at ${service_url}${NC}"
        return 1
    fi
}

# Function to get auth token if not provided
get_auth_token() {
    if [ -z "$AUTH_TOKEN" ]; then
        echo -e "${YELLOW}No auth token provided. Please set AUTH_TOKEN environment variable.${NC}"
        echo "Example: export AUTH_TOKEN='Bearer your_jwt_token_here'"
        return 1
    fi
    return 0
}

# Function to get user ID if not provided
get_user_id() {
    if [ -z "$USER_ID" ]; then
        echo -e "${YELLOW}No user ID provided. Please set USER_ID environment variable.${NC}"
        echo "Example: export USER_ID='your_user_id_here'"
        return 1
    fi
    return 0
}

# Function to clear all notifications
clear_all_notifications() {
    echo -e "${YELLOW}🗑️  Clearing all notifications...${NC}"
    
    local response=$(curl -s -X DELETE \
        -H "Authorization: ${AUTH_TOKEN}" \
        "${NOTIFICATION_SERVICE_URL}/api/notifications/clear-all")
    
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✅ All notifications cleared successfully${NC}"
        echo "Response: $response"
    else
        echo -e "${RED}❌ Failed to clear all notifications${NC}"
    fi
}

# Function to clear pending notifications
clear_pending_notifications() {
    echo -e "${YELLOW}🧹 Clearing pending notifications...${NC}"
    
    local response=$(curl -s -X DELETE \
        -H "Authorization: ${AUTH_TOKEN}" \
        "${NOTIFICATION_SERVICE_URL}/api/notifications/clear-pending")
    
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✅ Pending notifications cleared successfully${NC}"
        echo "Response: $response"
    else
        echo -e "${RED}❌ Failed to clear pending notifications${NC}"
    fi
}

# Function to clear notifications by type
clear_notifications_by_type() {
    local notification_type=$1
    echo -e "${YELLOW}🗑️  Clearing notifications of type: ${notification_type}${NC}"
    
    local response=$(curl -s -X DELETE \
        -H "Authorization: ${AUTH_TOKEN}" \
        "${NOTIFICATION_SERVICE_URL}/api/notifications/clear-by-type/${notification_type}")
    
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✅ Notifications of type '${notification_type}' cleared successfully${NC}"
        echo "Response: $response"
    else
        echo -e "${RED}❌ Failed to clear notifications of type '${notification_type}'${NC}"
    fi
}

# Function to get queue status
get_queue_status() {
    echo -e "${YELLOW}📊 Getting notification queue status...${NC}"
    
    local response=$(curl -s -X GET \
        -H "Authorization: ${AUTH_TOKEN}" \
        "${NOTIFICATION_SERVICE_URL}/api/notifications/queue-status")
    
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✅ Queue status retrieved successfully${NC}"
        echo "Response: $response" | jq '.' 2>/dev/null || echo "Response: $response"
    else
        echo -e "${RED}❌ Failed to get queue status${NC}"
    fi
}

# Function to clear Redis queues (if Redis is accessible)
clear_redis_queues() {
    echo -e "${YELLOW}🔴 Clearing Redis notification queues...${NC}"
    
    # Check if redis-cli is available
    if command -v redis-cli >/dev/null 2>&1; then
        local redis_url="${REDIS_URL:-redis://localhost:6379}"
        
        # Clear notification-related keys
        local keys_cleared=$(redis-cli -u "$redis_url" --scan --pattern "study_ai_events:*" | wc -l)
        redis-cli -u "$redis_url" --scan --pattern "study_ai_events:*" | xargs -r redis-cli -u "$redis_url" del
        
        echo -e "${GREEN}✅ Redis notification queues cleared${NC}"
        echo "Keys cleared: $keys_cleared"
    else
        echo -e "${YELLOW}⚠️  redis-cli not available, skipping Redis queue clearing${NC}"
    fi
}

# Function to show usage
show_usage() {
    echo "Usage: $0 [OPTIONS] [COMMAND]"
    echo ""
    echo "Commands:"
    echo "  all              Clear all notifications"
    echo "  pending          Clear pending/processing notifications"
    echo "  type <type>      Clear notifications by type (e.g., 'document_ready')"
    echo "  status           Show queue status"
    echo "  redis            Clear Redis notification queues"
    echo "  help             Show this help message"
    echo ""
    echo "Options:"
    echo "  --service-url    API Gateway URL (default: http://localhost:8000)"
    echo "  --auth-token     JWT auth token"
    echo "  --user-id        User ID for operations"
    echo ""
    echo "Environment Variables:"
    echo "  NOTIFICATION_SERVICE_URL  API Gateway URL (default: http://localhost:8000)"
    echo "  AUTH_TOKEN               JWT auth token"
    echo "  USER_ID                  User ID"
    echo "  REDIS_URL                Redis connection URL"
    echo ""
    echo "Examples:"
    echo "  $0 all                    # Clear all notifications"
    echo "  $0 pending                # Clear pending notifications"
    echo "  $0 type document_ready    # Clear document ready notifications"
    echo "  $0 status                 # Show queue status"
    echo "  export AUTH_TOKEN='Bearer token'; $0 all  # With auth token"
}

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --service-url)
            NOTIFICATION_SERVICE_URL="$2"
            shift 2
            ;;
        --auth-token)
            AUTH_TOKEN="$2"
            shift 2
            ;;
        --user-id)
            USER_ID="$2"
            shift 2
            ;;
        help|--help|-h)
            show_usage
            exit 0
            ;;
        *)
            COMMAND="$1"
            shift
            ;;
    esac
done

# Main execution
main() {
    # Check if API gateway is running
    if ! check_service "$NOTIFICATION_SERVICE_URL" "API Gateway"; then
        echo -e "${RED}Please start the API gateway first${NC}"
        exit 1
    fi
    
    # Check if we have the required parameters
    if ! get_auth_token; then
        exit 1
    fi
    
    # Execute command
    case "$COMMAND" in
        all)
            clear_all_notifications
            ;;
        pending)
            clear_pending_notifications
            ;;
        type)
            if [ -z "$1" ]; then
                echo -e "${RED}Please specify notification type${NC}"
                echo "Example: $0 type document_ready"
                exit 1
            fi
            clear_notifications_by_type "$1"
            ;;
        status)
            get_queue_status
            ;;
        redis)
            clear_redis_queues
            ;;
        "")
            echo -e "${YELLOW}No command specified. Use '$0 help' for usage information.${NC}"
            exit 1
            ;;
        *)
            echo -e "${RED}Unknown command: $COMMAND${NC}"
            echo "Use '$0 help' for usage information."
            exit 1
            ;;
    esac
}

# Run main function
main "$@"
