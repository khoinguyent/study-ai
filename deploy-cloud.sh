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
    echo ""
    echo -e "${YELLOW}📋 Setup Instructions:${NC}"
    echo -e "  1. Copy the example configuration:"
    echo -e "     cp env.cloud.example $CONFIG_FILE"
    echo -e "  2. Edit $CONFIG_FILE and configure:"
    echo -e "     - AWS credentials"
    echo -e "     - ElastiCache endpoint"
    echo -e "     - SQS queue URL"
    echo -e "     - Other infrastructure endpoints"
    echo -e "  3. Run this script again"
    echo ""
    exit 1
fi

# Load environment variables
echo -e "${BLUE}📋 Loading environment configuration...${NC}"
source "$CONFIG_FILE"

# Validate required environment variables
echo -e "${BLUE}🔍 Validating environment configuration...${NC}"

# Basic environment variables
required_vars=(
    "ENVIRONMENT"
    "INFRASTRUCTURE_PROVIDER"
    "MESSAGE_BROKER_TYPE"
    "TASK_QUEUE_TYPE"
)

# AWS credentials
required_vars+=(
    "AWS_REGION"
    "AWS_ACCESS_KEY_ID"
    "AWS_SECRET_ACCESS_KEY"
)

# Infrastructure endpoints
required_vars+=(
    "MESSAGE_BROKER_URL"
    "TASK_QUEUE_URL"
)

# Validate all required variables
missing_vars=()
for var in "${required_vars[@]}"; do
    if [ -z "${!var}" ]; then
        missing_vars+=("$var")
    fi
done

if [ ${#missing_vars[@]} -gt 0 ]; then
    echo -e "${RED}❌ Missing required environment variables:${NC}"
    for var in "${missing_vars[@]}"; do
        echo -e "  - $var"
    done
    echo ""
    echo -e "${YELLOW}📋 Configuration Guide:${NC}"
    echo -e "  The following variables must be set in $CONFIG_FILE:"
    echo ""
    echo -e "  ${BLUE}🔑 AWS Configuration:${NC}"
    echo -e "    AWS_REGION=us-east-1"
    echo -e "    AWS_ACCESS_KEY_ID=your-access-key"
    echo -e "    AWS_SECRET_ACCESS_KEY=your-secret-key"
    echo ""
    echo -e "  ${BLUE}📡 Infrastructure Endpoints:${NC}"
    echo -e "    MESSAGE_BROKER_URL=redis://your-elasticache-endpoint:6379"
    echo -e "    TASK_QUEUE_URL=https://sqs.us-east-1.amazonaws.com/account/queue"
    echo ""
    echo -e "  ${BLUE}🔧 Optional but Recommended:${NC}"
    echo -e "    REDIS_HOST=your-elasticache-endpoint"
    echo -e "    REDIS_PASSWORD=your-elasticache-password"
    echo -e "    SQS_QUEUE_URL=https://sqs.us-east-1.amazonaws.com/account/queue"
    echo ""
    echo -e "  ${YELLOW}💡 Get these values from:${NC}"
    echo -e "    - AWS Console → ElastiCache → Redis clusters"
    echo -e "    - AWS Console → SQS → Queues"
    echo -e "    - AWS Console → IAM → Users → Access keys"
    echo ""
    exit 1
fi

echo -e "${GREEN}✅ Environment configuration validated${NC}"

# Show current configuration
echo -e "${BLUE}📊 Current Configuration:${NC}"
echo -e "  🌍 Environment: $ENVIRONMENT"
echo -e "  ☁️  Provider: $INFRASTRUCTURE_PROVIDER"
echo -e "  📡 Message Broker: $MESSAGE_BROKER_TYPE"
echo -e "  📋 Task Queue: $TASK_QUEUE_TYPE"
echo -e "  🌐 AWS Region: $AWS_REGION"
echo -e "  🔑 AWS Access Key: ${AWS_ACCESS_KEY_ID:0:8}..."
echo -e "  📡 Broker URL: $MESSAGE_BROKER_URL"
echo -e "  📋 Queue URL: $TASK_QUEUE_URL"
echo ""

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
echo ""
echo -e "${BLUE}🔍 Troubleshooting:${NC}"
echo -e "  If services fail to start, check:"
echo -e "  1. AWS credentials and permissions"
echo -e "  2. ElastiCache endpoint accessibility"
echo -e "  3. SQS queue permissions"
echo -e "  4. Network connectivity to AWS services"
