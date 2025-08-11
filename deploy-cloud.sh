#!/bin/bash

# Cloud Deployment Script for Study AI Platform
# This script deploys the platform to cloud environment using infrastructure abstraction

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
ENVIRONMENT=${ENVIRONMENT:-"cloud"}
INFRASTRUCTURE_PROVIDER=${INFRASTRUCTURE_PROVIDER:-"aws"}
CONFIG_FILE="env.cloud"

echo -e "${BLUE}🚀 Study AI Platform Cloud Deployment${NC}"
echo -e "${BLUE}=====================================${NC}"
echo ""

# Check if configuration file exists
if [ ! -f "$CONFIG_FILE" ]; then
    echo -e "${RED}❌ Configuration file $CONFIG_FILE not found!${NC}"
    echo -e "${YELLOW}Please copy env.cloud.example to $CONFIG_FILE and update the values.${NC}"
    exit 1
fi

# Load environment variables
echo -e "${BLUE}📋 Loading environment configuration...${NC}"
source "$CONFIG_FILE"

# Validate required environment variables
echo -e "${BLUE}🔍 Validating environment configuration...${NC}"

required_vars=(
    "ENVIRONMENT"
    "INFRASTRUCTURE_PROVIDER"
    "MESSAGE_BROKER_TYPE"
    "TASK_QUEUE_TYPE"
    "AWS_REGION"
    "AWS_ACCESS_KEY_ID"
    "AWS_SECRET_ACCESS_KEY"
)

for var in "${required_vars[@]}"; do
    if [ -z "${!var}" ]; then
        echo -e "${RED}❌ Required environment variable $var is not set!${NC}"
        exit 1
    fi
done

echo -e "${GREEN}✅ Environment configuration validated${NC}"

# Check if Docker is running
echo -e "${BLUE}🐳 Checking Docker status...${NC}"
if ! docker info > /dev/null 2>&1; then
    echo -e "${RED}❌ Docker is not running!${NC}"
    exit 1
fi
echo -e "${GREEN}✅ Docker is running${NC}"

# Check if docker-compose is available
if ! command -v docker-compose &> /dev/null; then
    echo -e "${RED}❌ docker-compose is not installed!${NC}"
    exit 1
fi

# Build and deploy services
echo -e "${BLUE}🏗️  Building and deploying services...${NC}"

# Stop any existing containers
echo -e "${YELLOW}🛑 Stopping existing containers...${NC}"
docker-compose -f docker-compose.cloud.yml down --remove-orphans || true

# Build images
echo -e "${YELLOW}🔨 Building Docker images...${NC}"
docker-compose -f docker-compose.cloud.yml build --no-cache

# Start services
echo -e "${YELLOW}🚀 Starting services...${NC}"
docker-compose -f docker-compose.cloud.yml up -d

# Wait for services to be ready
echo -e "${YELLOW}⏳ Waiting for services to be ready...${NC}"
sleep 30

# Check service health
echo -e "${BLUE}🏥 Checking service health...${NC}"

services=(
    "api-gateway"
    "auth-service"
    "document-service"
    "indexing-service"
    "quiz-service"
    "notification-service"
    "leaf-quiz-service"
    "web"
)

all_healthy=true

for service in "${services[@]}"; do
    container_name="study-ai-${service}-cloud"
    
    if docker ps | grep -q "$container_name"; then
        echo -e "${GREEN}✅ $service is running${NC}"
    else
        echo -e "${RED}❌ $service is not running${NC}"
        all_healthy=false
    fi
done

if [ "$all_healthy" = true ]; then
    echo -e "${GREEN}🎉 All services are running successfully!${NC}"
    echo ""
    echo -e "${BLUE}📊 Service Status:${NC}"
    echo -e "  🌐 API Gateway: http://localhost:8000"
    echo -e "  🔐 Auth Service: http://localhost:8001"
    echo -e "  📄 Document Service: http://localhost:8002"
    echo -e "  🔍 Indexing Service: http://localhost:8003"
    echo -e "  ❓ Quiz Service: http://localhost:8004"
    echo -e "  🔔 Notification Service: http://localhost:8005"
    echo -e "  🍃 Leaf Quiz Service: http://localhost:8006"
    echo -e "  🌍 Web Frontend: http://localhost:3000"
    echo ""
    echo -e "${BLUE}🔧 Infrastructure:${NC}"
    echo -e "  📡 Message Broker: $MESSAGE_BROKER_TYPE"
    echo -e "  📋 Task Queue: $TASK_QUEUE_TYPE"
    echo -e "  ☁️  Provider: $INFRASTRUCTURE_PROVIDER"
    echo -e "  🌍 Region: $AWS_REGION"
    echo ""
    echo -e "${GREEN}🚀 Deployment completed successfully!${NC}"
else
    echo -e "${RED}❌ Some services failed to start. Check logs with:${NC}"
    echo -e "${YELLOW}docker-compose -f docker-compose.cloud.yml logs${NC}"
    exit 1
fi

# Show logs for monitoring
echo ""
echo -e "${BLUE}📋 Recent logs (last 20 lines):${NC}"
docker-compose -f docker-compose.cloud.yml logs --tail=20

echo ""
echo -e "${BLUE}📚 Useful commands:${NC}"
echo -e "  📊 View logs: docker-compose -f docker-compose.cloud.yml logs -f"
echo -e "  🛑 Stop services: docker-compose -f docker-compose.cloud.yml down"
echo -e "  🔄 Restart services: docker-compose -f docker-compose.cloud.yml restart"
echo -e "  🧹 Clean up: docker-compose -f docker-compose.cloud.yml down --volumes --remove-orphans"
