#!/bin/bash

# Study AI - Event System Test Script
# This script tests the event-driven architecture and real-time notifications

set -e

# Color definitions
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Helper functions
print_header() {
    echo -e "${BLUE}🔧 $1${NC}"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

print_status() {
    echo -e "${BLUE}📋 $1${NC}"
}

# Check if services are running
check_services() {
    print_header "Checking Service Status"
    echo "============================="
    
    services=(
        "api-gateway:8000"
        "auth-service:8001"
        "document-service:8002"
        "indexing-service:8003"
        "quiz-service:8004"
        "notification-service:8005"
        "redis:6379"
    )
    
    all_running=true
    
    for service in "${services[@]}"; do
        service_name=$(echo $service | cut -d: -f1)
        service_port=$(echo $service | cut -d: -f2)
        
        if curl -s http://localhost:$service_port/health > /dev/null 2>&1; then
            print_success "$service_name is running"
        else
            print_error "$service_name is not accessible"
            all_running=false
        fi
    done
    
    if [ "$all_running" = false ]; then
        print_error "Some services are not running. Please start the development environment:"
        print_warning "  ./scripts/setup-dev.sh"
        exit 1
    fi
    
    print_success "All services are running!"
}

# Test event publishing
test_event_publishing() {
    print_header "Testing Event Publishing"
    echo "============================="
    
    # Test Redis connection
    print_status "Testing Redis connection..."
    if redis-cli ping > /dev/null 2>&1; then
        print_success "Redis is accessible"
    else
        print_error "Redis is not accessible"
        return 1
    fi
    
    # Test event publishing via API
    print_status "Testing document upload event..."
    
    # First, get auth token
    print_status "Getting authentication token..."
    auth_response=$(curl -s -X POST http://localhost:8000/auth/login \
        -H "Content-Type: application/json" \
        -d '{"email": "test@test.com", "password": "test123"}')
    
    if echo "$auth_response" | jq -e '.access_token' > /dev/null; then
        token=$(echo "$auth_response" | jq -r '.access_token')
        print_success "Authentication successful"
    else
        print_error "Authentication failed"
        return 1
    fi
    
    # Test document upload (this will trigger events)
    print_status "Testing document upload to trigger events..."
    
    # Create a test file
    echo "This is a test document for event testing." > /tmp/test_document.txt
    
    upload_response=$(curl -s -X POST http://localhost:8000/documents/upload \
        -H "Authorization: Bearer $token" \
        -F "file=@/tmp/test_document.txt")
    
    if echo "$upload_response" | jq -e '.id' > /dev/null; then
        document_id=$(echo "$upload_response" | jq -r '.id')
        print_success "Document upload successful (ID: $document_id)"
    else
        print_error "Document upload failed"
        echo "Response: $upload_response"
        return 1
    fi
    
    # Clean up test file
    rm -f /tmp/test_document.txt
}

# Monitor events in real-time
monitor_events() {
    print_header "Monitoring Events in Real-Time"
    echo "===================================="
    
    print_status "Starting event monitoring (press Ctrl+C to stop)..."
    print_warning "This will show all events published to Redis pub/sub"
    echo ""
    
    # Monitor Redis pub/sub for study_ai_events
    redis-cli monitor | grep "study_ai_events" || true
}

# Test WebSocket notifications
test_websocket_notifications() {
    print_header "Testing WebSocket Notifications"
    echo "====================================="
    
    print_status "Testing WebSocket connection..."
    
    # Check if wscat is available
    if ! command -v wscat &> /dev/null; then
        print_warning "wscat not found. Installing..."
        npm install -g wscat
    fi
    
    print_status "Connecting to WebSocket endpoint..."
    print_warning "This will open a WebSocket connection to test notifications"
    echo ""
    
    # Connect to WebSocket (this will stay open for testing)
    wscat -c ws://localhost:8000/ws/test@test.com || true
}

# Test task status updates
test_task_status() {
    print_header "Testing Task Status Updates"
    echo "================================"
    
    print_status "Getting authentication token..."
    auth_response=$(curl -s -X POST http://localhost:8000/auth/login \
        -H "Content-Type: application/json" \
        -d '{"email": "test@test.com", "password": "test123"}')
    
    if echo "$auth_response" | jq -e '.access_token' > /dev/null; then
        token=$(echo "$auth_response" | jq -r '.access_token')
        print_success "Authentication successful"
    else
        print_error "Authentication failed"
        return 1
    fi
    
    # Test task status creation
    print_status "Creating test task status..."
    task_response=$(curl -s -X POST http://localhost:8000/notifications/task-status \
        -H "Authorization: Bearer $token" \
        -H "Content-Type: application/json" \
        -d '{
            "task_id": "test_task_123",
            "user_id": "test@test.com",
            "task_type": "test_processing",
            "status": "processing",
            "progress": 25,
            "message": "Testing task status updates"
        }')
    
    if echo "$task_response" | jq -e '.task_id' > /dev/null; then
        print_success "Task status created successfully"
    else
        print_error "Task status creation failed"
        echo "Response: $task_response"
        return 1
    fi
    
    # Test task status update
    print_status "Updating task status..."
    update_response=$(curl -s -X PUT http://localhost:8000/notifications/task-status/test_task_123 \
        -H "Authorization: Bearer $token" \
        -H "Content-Type: application/json" \
        -d '{
            "status": "completed",
            "progress": 100,
            "message": "Task completed successfully"
        }')
    
    if echo "$update_response" | jq -e '.status' > /dev/null; then
        print_success "Task status updated successfully"
    else
        print_error "Task status update failed"
        echo "Response: $update_response"
        return 1
    fi
}

# Show event system status
show_status() {
    print_header "Event System Status"
    echo "======================"
    
    # Check Redis pub/sub channels
    print_status "Redis Pub/Sub Channels:"
    channels=$(redis-cli pubsub channels "study_ai_events:*" 2>/dev/null || echo "No channels found")
    if [ "$channels" != "No channels found" ]; then
        echo "$channels" | while read channel; do
            print_success "  $channel"
        done
    else
        print_warning "  No active event channels"
    fi
    
    echo ""
    
    # Check Redis info
    print_status "Redis Info:"
    redis_info=$(redis-cli info server 2>/dev/null | grep -E "(redis_version|connected_clients|used_memory_human)" || echo "Redis not accessible")
    echo "$redis_info"
    
    echo ""
    
    # Check service health
    print_status "Service Health:"
    services=(
        "API Gateway:8000"
        "Auth Service:8001"
        "Document Service:8002"
        "Indexing Service:8003"
        "Quiz Service:8004"
        "Notification Service:8005"
    )
    
    for service in "${services[@]}"; do
        service_name=$(echo $service | cut -d: -f1)
        service_port=$(echo $service | cut -d: -f2)
        
        if curl -s http://localhost:$service_port/health > /dev/null 2>&1; then
            print_success "$service_name: Healthy"
        else
            print_error "$service_name: Unhealthy"
        fi
    done
}

# Main script logic
case "${1:-help}" in
    "check")
        check_services
        ;;
    "publish")
        test_event_publishing
        ;;
    "monitor")
        monitor_events
        ;;
    "websocket")
        test_websocket_notifications
        ;;
    "task")
        test_task_status
        ;;
    "status")
        show_status
        ;;
    "all")
        check_services
        echo ""
        test_event_publishing
        echo ""
        show_status
        ;;
    "help"|*)
        echo "Study AI - Event System Test Script"
        echo "=================================="
        echo ""
        echo "Usage: $0 <command>"
        echo ""
        echo "Commands:"
        echo "  check      - Check if all services are running"
        echo "  publish    - Test event publishing with document upload"
        echo "  monitor    - Monitor events in real-time"
        echo "  websocket  - Test WebSocket notifications"
        echo "  task       - Test task status updates"
        echo "  status     - Show event system status"
        echo "  all        - Run all tests"
        echo "  help       - Show this help message"
        echo ""
        echo "Examples:"
        echo "  $0 check"
        echo "  $0 publish"
        echo "  $0 monitor"
        echo "  $0 all"
        ;;
esac 