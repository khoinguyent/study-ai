#!/bin/bash

# CI/CD Deployment Script for Study AI Platform
# This script handles deployment to different environments

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
ENVIRONMENT="${ENVIRONMENT:-staging}"
DEPLOYMENT_TYPE="${DEPLOYMENT_TYPE:-rolling}"

# Default values
DOCKER_COMPOSE_FILE="docker-compose.cloud.yml"
ENV_FILE="env.cloud"
REGISTRY="ghcr.io"
IMAGE_TAG="${IMAGE_TAG:-latest}"

echo -e "${BLUE}🚀 Study AI Platform CI/CD Deployment${NC}"
echo -e "${BLUE}=====================================${NC}"
echo ""

# Function to display usage
usage() {
    echo "Usage: $0 [OPTIONS]"
    echo ""
    echo "Options:"
    echo "  -e, --environment ENV    Deployment environment (staging|production)"
    echo "  -t, --type TYPE          Deployment type (rolling|blue-green|canary)"
    echo "  -f, --file FILE          Docker Compose file to use"
    echo "  -r, --registry REG       Container registry (default: ghcr.io)"
    echo "  -i, --image-tag TAG      Docker image tag to deploy"
    echo "  -h, --help               Show this help message"
    echo ""
    echo "Environment Variables:"
    echo "  ENVIRONMENT              Deployment environment"
    echo "  DEPLOYMENT_TYPE          Deployment strategy"
    echo "  AWS_ACCESS_KEY_ID        AWS access key"
    echo "  AWS_SECRET_ACCESS_KEY    AWS secret key"
    echo "  AWS_REGION               AWS region"
    echo ""
    echo "Examples:"
    echo "  $0 -e production -t rolling"
    echo "  $0 --environment staging --type blue-green"
    echo "  ENVIRONMENT=production $0"
}

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        -e|--environment)
            ENVIRONMENT="$2"
            shift 2
            ;;
        -t|--type)
            DEPLOYMENT_TYPE="$2"
            shift 2
            ;;
        -f|--file)
            DOCKER_COMPOSE_FILE="$2"
            shift 2
            ;;
        -r|--registry)
            REGISTRY="$2"
            shift 2
            ;;
        -i|--image-tag)
            IMAGE_TAG="$2"
            shift 2
            ;;
        -h|--help)
            usage
            exit 0
            ;;
        *)
            echo -e "${RED}❌ Unknown option: $1${NC}"
            usage
            exit 1
            ;;
    esac
done

# Validate environment
if [[ ! "$ENVIRONMENT" =~ ^(staging|production)$ ]]; then
    echo -e "${RED}❌ Invalid environment: $ENVIRONMENT${NC}"
    echo -e "${YELLOW}Valid environments: staging, production${NC}"
    exit 1
fi

# Validate deployment type
if [[ ! "$DEPLOYMENT_TYPE" =~ ^(rolling|blue-green|canary)$ ]]; then
    echo -e "${RED}❌ Invalid deployment type: $DEPLOYMENT_TYPE${NC}"
    echo -e "${YELLOW}Valid types: rolling, blue-green, canary${NC}"
    exit 1
fi

echo -e "${BLUE}📋 Deployment Configuration:${NC}"
echo -e "  Environment: ${GREEN}$ENVIRONMENT${NC}"
echo -e "  Deployment Type: ${GREEN}$DEPLOYMENT_TYPE${NC}"
echo -e "  Docker Compose: ${GREEN}$DOCKER_COMPOSE_FILE${NC}"
echo -e "  Registry: ${GREEN}$REGISTRY${NC}"
echo -e "  Image Tag: ${GREEN}$IMAGE_TAG${NC}"
echo ""

# Check if we're in CI/CD environment
if [[ -n "$CI" ]]; then
    echo -e "${BLUE}🔧 CI/CD Environment Detected${NC}"
    
    # Set environment-specific variables
    case "$ENVIRONMENT" in
        staging)
            export AWS_ACCESS_KEY_ID="$AWS_ACCESS_KEY_ID_STAGING"
            export AWS_SECRET_ACCESS_KEY="$AWS_SECRET_ACCESS_KEY_STAGING"
            export AWS_REGION="$AWS_REGION_STAGING"
            ;;
        production)
            export AWS_ACCESS_KEY_ID="$AWS_ACCESS_KEY_ID_PROD"
            export AWS_SECRET_ACCESS_KEY="$AWS_SECRET_ACCESS_KEY_PROD"
            export AWS_REGION="$AWS_REGION_PROD"
            ;;
    esac
fi

# Validate AWS credentials
if [[ -z "$AWS_ACCESS_KEY_ID" || -z "$AWS_SECRET_ACCESS_KEY" || -z "$AWS_REGION" ]]; then
    echo -e "${RED}❌ Missing AWS credentials${NC}"
    echo -e "${YELLOW}Please set AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, and AWS_REGION${NC}"
    exit 1
fi

echo -e "${GREEN}✅ AWS credentials configured for region: $AWS_REGION${NC}"

# Change to project root
cd "$PROJECT_ROOT"

# Check if required files exist
if [[ ! -f "$DOCKER_COMPOSE_FILE" ]]; then
    echo -e "${RED}❌ Docker Compose file not found: $DOCKER_COMPOSE_FILE${NC}"
    exit 1
fi

if [[ ! -f "$ENV_FILE" ]]; then
    echo -e "${RED}❌ Environment file not found: $ENV_FILE${NC}"
    echo -e "${YELLOW}Please run ./auto-fill-cloud-config.sh first${NC}"
    exit 1
fi

echo -e "${GREEN}✅ Required files found${NC}"

# Function to run health checks
run_health_checks() {
    local service_name="$1"
    local max_attempts=30
    local attempt=1
    
    echo -e "${BLUE}🏥 Running health checks for $service_name...${NC}"
    
    while [[ $attempt -le $max_attempts ]]; do
        if docker-compose -f "$DOCKER_COMPOSE_FILE" ps "$service_name" | grep -q "healthy"; then
            echo -e "${GREEN}✅ $service_name is healthy${NC}"
            return 0
        fi
        
        echo -e "${YELLOW}⏳ Attempt $attempt/$max_attempts: $service_name not ready yet...${NC}"
        sleep 10
        ((attempt++))
    done
    
    echo -e "${RED}❌ $service_name failed health checks after $max_attempts attempts${NC}"
    return 1
}

# Function to deploy with rolling strategy
deploy_rolling() {
    echo -e "${BLUE}🔄 Deploying with rolling strategy...${NC}"
    
    # Pull latest images
    echo -e "${BLUE}📥 Pulling latest images...${NC}"
    docker-compose -f "$DOCKER_COMPOSE_FILE" pull
    
    # Deploy with rolling update
    echo -e "${BLUE}🚀 Starting rolling deployment...${NC}"
    docker-compose -f "$DOCKER_COMPOSE_FILE" up -d --remove-orphans
    
    # Wait for services to be healthy
    echo -e "${BLUE}⏳ Waiting for services to be healthy...${NC}"
    
    local services=("auth-db" "document-db" "indexing-db" "quiz-db" "notification-db")
    for service in "${services[@]}"; do
        if ! run_health_checks "$service"; then
            echo -e "${RED}❌ Deployment failed: $service is not healthy${NC}"
            exit 1
        fi
    done
    
    local app_services=("auth-service" "document-service" "indexing-service" "quiz-service" "notification-service" "leaf-quiz-service" "api-gateway" "web")
    for service in "${app_services[@]}"; do
        if ! run_health_checks "$service"; then
            echo -e "${RED}❌ Deployment failed: $service is not healthy${NC}"
            exit 1
        fi
    done
    
    echo -e "${GREEN}✅ Rolling deployment completed successfully!${NC}"
}

# Function to deploy with blue-green strategy
deploy_blue_green() {
    echo -e "${BLUE}🔵🟢 Deploying with blue-green strategy...${NC}"
    
    # This is a simplified blue-green deployment
    # In production, you'd want more sophisticated traffic switching
    
    echo -e "${BLUE}📥 Pulling latest images...${NC}"
    docker-compose -f "$DOCKER_COMPOSE_FILE" pull
    
    echo -e "${BLUE}🚀 Starting new deployment...${NC}"
    docker-compose -f "$DOCKER_COMPOSE_FILE" up -d --remove-orphans
    
    # Wait for new deployment to be healthy
    echo -e "${BLUE}⏳ Waiting for new deployment to be healthy...${NC}"
    
    local services=("auth-db" "document-db" "indexing-db" "quiz-db" "notification-db")
    for service in "${services[@]}"; do
        if ! run_health_checks "$service"; then
            echo -e "${RED}❌ Blue-green deployment failed: $service is not healthy${NC}"
            exit 1
        fi
    done
    
    echo -e "${GREEN}✅ Blue-green deployment completed successfully!${NC}"
}

# Function to deploy with canary strategy
deploy_canary() {
    echo -e "${BLUE}🐦 Deploying with canary strategy...${NC}"
    
    # This is a simplified canary deployment
    # In production, you'd want traffic splitting and gradual rollout
    
    echo -e "${BLUE}📥 Pulling latest images...${NC}"
    docker-compose -f "$DOCKER_COMPOSE_FILE" pull
    
    echo -e "${BLUE}🚀 Starting canary deployment...${NC}"
    docker-compose -f "$DOCKER_COMPOSE_FILE" up -d --remove-orphans
    
    # Wait for canary to be healthy
    echo -e "${BLUE}⏳ Waiting for canary deployment to be healthy...${NC}"
    
    local services=("auth-db" "document-db" "indexing-db" "quiz-db" "notification-db")
    for service in "${services[@]}"; do
        if ! run_health_checks "$service"; then
            echo -e "${RED}❌ Canary deployment failed: $service is not healthy${NC}"
            exit 1
        fi
    done
    
    echo -e "${GREEN}✅ Canary deployment completed successfully!${NC}"
}

# Function to run smoke tests
run_smoke_tests() {
    echo -e "${BLUE}🧪 Running smoke tests...${NC}"
    
    # Test API Gateway
    local api_url="http://localhost:8000/health"
    local max_attempts=10
    local attempt=1
    
    while [[ $attempt -le $max_attempts ]]; do
        if curl -f -s "$api_url" > /dev/null; then
            echo -e "${GREEN}✅ API Gateway health check passed${NC}"
            break
        fi
        
        if [[ $attempt -eq $max_attempts ]]; then
            echo -e "${RED}❌ API Gateway health check failed after $max_attempts attempts${NC}"
            return 1
        fi
        
        echo -e "${YELLOW}⏳ Attempt $attempt/$max_attempts: API Gateway not ready...${NC}"
        sleep 5
        ((attempt++))
    done
    
    # Test web frontend
    local web_url="http://localhost:3000"
    attempt=1
    
    while [[ $attempt -le $max_attempts ]]; do
        if curl -f -s "$web_url" > /dev/null; then
            echo -e "${GREEN}✅ Web frontend health check passed${NC}"
            break
        fi
        
        if [[ $attempt -eq $max_attempts ]]; then
            echo -e "${RED}❌ Web frontend health check failed after $max_attempts attempts${NC}"
            return 1
        fi
        
        echo -e "${YELLOW}⏳ Attempt $attempt/$max_attempts: Web frontend not ready...${NC}"
        sleep 5
        ((attempt++))
    done
    
    echo -e "${GREEN}✅ All smoke tests passed!${NC}"
    return 0
}

# Main deployment logic
echo -e "${BLUE}🚀 Starting deployment to $ENVIRONMENT environment...${NC}"

case "$DEPLOYMENT_TYPE" in
    rolling)
        deploy_rolling
        ;;
    blue-green)
        deploy_blue_green
        ;;
    canary)
        deploy_canary
        ;;
esac

# Run smoke tests
if run_smoke_tests; then
    echo -e "${GREEN}🎉 Deployment to $ENVIRONMENT completed successfully!${NC}"
    
    # Show service status
    echo -e "${BLUE}📊 Service Status:${NC}"
    docker-compose -f "$DOCKER_COMPOSE_FILE" ps
    
    # Show logs for any failed services
    echo -e "${BLUE}📋 Checking for any failed services...${NC}"
    local failed_services=$(docker-compose -f "$DOCKER_COMPOSE_FILE" ps --filter "status=exited" --format "table {{.Name}}\t{{.Status}}")
    
    if [[ -n "$failed_services" ]]; then
        echo -e "${YELLOW}⚠️  Some services may have failed:${NC}"
        echo "$failed_services"
    else
        echo -e "${GREEN}✅ All services are running successfully!${NC}"
    fi
    
    exit 0
else
    echo -e "${RED}❌ Deployment failed: smoke tests did not pass${NC}"
    
    # Show logs for debugging
    echo -e "${BLUE}📋 Recent logs for debugging:${NC}"
    docker-compose -f "$DOCKER_COMPOSE_FILE" logs --tail=50
    
    exit 1
fi
