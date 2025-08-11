#!/bin/bash

# Local Development Deployment Script for Study AI Platform
# This script handles local development environment setup and deployment

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
ENVIRONMENT="local"
DOCKER_COMPOSE_FILE="docker-compose.yml"
ENV_FILE="env.local"

echo -e "${BLUE}🏠 Local Development Deployment Script${NC}"
echo -e "${BLUE}=====================================${NC}"
echo ""

# Function to display usage
usage() {
    echo "Usage: $0 [OPTIONS]"
    echo ""
    echo "Options:"
    echo "  -s, --service SERVICE    Deploy specific service only"
    echo "  -b, --build             Force rebuild all images"
    echo "  -c, --clean             Clean up before deployment"
    echo "  -d, --detach            Run in background"
    echo "  -h, --help              Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0                      # Deploy all services"
    echo "  $0 -s api-gateway      # Deploy only API Gateway"
    echo "  $0 -b                  # Rebuild and deploy all"
    echo "  $0 -c                  # Clean and deploy"
}

# Parse command line arguments
BUILD=false
CLEAN=false
DETACH=false
SERVICE=""

while [[ $# -gt 0 ]]; do
    case $1 in
        -s|--service)
            SERVICE="$2"
            shift 2
            ;;
        -b|--build)
            BUILD=true
            shift
            ;;
        -c|--clean)
            CLEAN=true
            shift
            ;;
        -d|--detach)
            DETACH=true
            shift
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

# Change to project root
cd "$PROJECT_ROOT"

# Check if required files exist
if [[ ! -f "$DOCKER_COMPOSE_FILE" ]]; then
    echo -e "${RED}❌ Docker Compose file not found: $DOCKER_COMPOSE_FILE${NC}"
    exit 1
fi

if [[ ! -f "$ENV_FILE" ]]; then
    echo -e "${YELLOW}⚠️  Local environment file not found: $ENV_FILE${NC}"
    echo -e "${BLUE}Creating from template...${NC}"
    if [[ -f "env.local.example" ]]; then
        cp env.local.example "$ENV_FILE"
        echo -e "${GREEN}✅ Created $ENV_FILE from template${NC}"
        echo -e "${YELLOW}Please review and update the configuration as needed${NC}"
    else
        echo -e "${RED}❌ env.local.example not found${NC}"
        exit 1
    fi
fi

echo -e "${GREEN}✅ Required files found${NC}"
echo ""

# Display configuration
echo -e "${BLUE}📋 Deployment Configuration:${NC}"
echo -e "  Environment: ${GREEN}$ENVIRONMENT${NC}"
echo -e "  Docker Compose: ${GREEN}$DOCKER_COMPOSE_FILE${NC}"
echo -e "  Environment File: ${GREEN}$ENV_FILE${NC}"
echo -e "  Build Images: ${GREEN}$BUILD${NC}"
echo -e "  Clean First: ${GREEN}$CLEAN${NC}"
echo -e "  Run Detached: ${GREEN}$DETACH${NC}"
if [[ -n "$SERVICE" ]]; then
    echo -e "  Service Only: ${GREEN}$SERVICE${NC}"
fi
echo ""

# Function to check if Docker is running
check_docker() {
    if ! docker info > /dev/null 2>&1; then
        echo -e "${RED}❌ Docker is not running${NC}"
        echo -e "${YELLOW}Please start Docker Desktop or Docker daemon${NC}"
        exit 1
    fi
    echo -e "${GREEN}✅ Docker is running${NC}"
}

# Function to check available ports
check_ports() {
    local ports=("8000" "8001" "8002" "8003" "8004" "8005" "8006" "3000" "5432" "5433" "5434" "5435" "5437" "6379" "9000" "9001" "11434")
    local conflicts=()
    
    echo -e "${BLUE}🔍 Checking port availability...${NC}"
    
    for port in "${ports[@]}"; do
        if lsof -Pi :$port -sTCP:LISTEN -t >/dev/null 2>&1; then
            conflicts+=("$port")
        fi
    done
    
    if [[ ${#conflicts[@]} -gt 0 ]]; then
        echo -e "${YELLOW}⚠️  Port conflicts detected:${NC}"
        for port in "${conflicts[@]}"; do
            echo -e "  Port $port is already in use"
        done
        echo ""
        echo -e "${YELLOW}You may need to stop conflicting services or change ports${NC}"
        echo -e "${BLUE}Common solutions:${NC}"
        echo -e "  - Stop other Docker containers: docker stop \$(docker ps -q)"
        echo -e "  - Kill processes on specific ports: lsof -ti:$port | xargs kill -9"
        echo ""
        read -p "Continue anyway? (y/N): " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            exit 1
        fi
    else
        echo -e "${GREEN}✅ All ports are available${NC}"
    fi
}

# Function to clean up
cleanup() {
    echo -e "${BLUE}🧹 Cleaning up...${NC}"
    
    # Stop existing containers
    if docker-compose -f "$DOCKER_COMPOSE_FILE" ps -q | grep -q .; then
        echo -e "${BLUE}  Stopping existing containers...${NC}"
        docker-compose -f "$DOCKER_COMPOSE_FILE" down
    fi
    
    # Remove volumes if requested
    if [[ "$CLEAN" == true ]]; then
        echo -e "${BLUE}  Removing volumes...${NC}"
        docker-compose -f "$DOCKER_COMPOSE_FILE" down --volumes --remove-orphans
        echo -e "${BLUE}  Removing images...${NC}"
        docker-compose -f "$DOCKER_COMPOSE_FILE" down --rmi all
    fi
    
    # Clean up dangling images and containers
    echo -e "${BLUE}  Cleaning up Docker system...${NC}"
    docker system prune -f
    
    echo -e "${GREEN}✅ Cleanup completed${NC}"
}

# Function to build images
build_images() {
    if [[ "$BUILD" == true ]]; then
        echo -e "${BLUE}🔨 Building Docker images...${NC}"
        
        if [[ -n "$SERVICE" ]]; then
            echo -e "${BLUE}  Building $SERVICE...${NC}"
            docker-compose -f "$DOCKER_COMPOSE_FILE" build --no-cache "$SERVICE"
        else
            echo -e "${BLUE}  Building all services...${NC}"
            docker-compose -f "$DOCKOSE_FILE" build --no-cache
        fi
        
        echo -e "${GREEN}✅ Build completed${NC}"
    fi
}

# Function to deploy services
deploy_services() {
    echo -e "${BLUE}🚀 Deploying services...${NC}"
    
    local compose_cmd="docker-compose -f $DOCKER_COMPOSE_FILE"
    
    if [[ -n "$SERVICE" ]]; then
        echo -e "${BLUE}  Deploying $SERVICE only...${NC}"
        if [[ "$DETACH" == true ]]; then
            $compose_cmd up -d "$SERVICE"
        else
            $compose_cmd up "$SERVICE"
        fi
    else
        echo -e "${BLUE}  Deploying all services...${NC}"
        if [[ "$DETACH" == true ]]; then
            $compose_cmd up -d
        else
            $compose_cmd up
        fi
    fi
}

# Function to wait for services
wait_for_services() {
    if [[ "$DETACH" == true ]]; then
        echo -e "${BLUE}⏳ Waiting for services to be ready...${NC}"
        
        local services=("auth-db" "document-db" "indexing-db" "quiz-db" "notification-db" "redis" "minio" "ollama")
        local max_attempts=30
        
        for service in "${services[@]}"; do
            local attempt=1
            echo -e "${BLUE}  Waiting for $service...${NC}"
            
            while [[ $attempt -le $max_attempts ]]; do
                if docker-compose -f "$DOCKER_COMPOSE_FILE" ps "$service" | grep -q "healthy\|Up"; then
                    echo -e "${GREEN}    ✅ $service is ready${NC}"
                    break
                fi
                
                if [[ $attempt -eq $max_attempts ]]; then
                    echo -e "${YELLOW}    ⚠️  $service may not be fully ready${NC}"
                fi
                
                echo -e "${YELLOW}    ⏳ Attempt $attempt/$max_attempts...${NC}"
                sleep 5
                ((attempt++))
            done
        done
        
        echo -e "${GREEN}✅ All services are starting up${NC}"
    fi
}

# Function to show status
show_status() {
    echo ""
    echo -e "${BLUE}📊 Service Status:${NC}"
    docker-compose -f "$DOCKER_COMPOSE_FILE" ps
    
    echo ""
    echo -e "${BLUE}🌐 Service URLs:${NC}"
    echo -e "  API Gateway: ${GREEN}http://localhost:8000${NC}"
    echo -e "  Auth Service: ${GREEN}http://localhost:8001${NC}"
    echo -e "  Document Service: ${GREEN}http://localhost:8002${NC}"
    echo -e "  Indexing Service: ${GREEN}http://localhost:8003${NC}"
    echo -e "  Quiz Service: ${GREEN}http://localhost:8004${NC}"
    echo -e "  Notification Service: ${GREEN}http://localhost:8005${NC}"
    echo -e "  Leaf Quiz Service: ${GREEN}http://localhost:8006${NC}"
    echo -e "  Web Frontend: ${GREEN}http://localhost:3000${NC}"
    echo -e "  MinIO Console: ${GREEN}http://localhost:9001${NC}"
    echo -e "  Ollama: ${GREEN}http://localhost:11434${NC}"
    
    echo ""
    echo -e "${BLUE}🗄️  Database URLs:${NC}"
    echo -e "  Auth DB: ${GREEN}localhost:5432${NC}"
    echo -e "  Document DB: ${GREEN}localhost:5433${NC}"
    echo -e "  Indexing DB: ${GREEN}localhost:5434${NC}"
    echo -e "  Quiz DB: ${GREEN}localhost:5435${NC}"
    echo -e "  Notification DB: ${GREEN}localhost:5437${NC}"
    echo -e "  Redis: ${GREEN}localhost:6379${NC}"
    
    echo ""
    echo -e "${BLUE}🔧 Useful Commands:${NC}"
    echo -e "  View logs: ${GREEN}docker-compose -f $DOCKER_COMPOSE_FILE logs -f${NC}"
    echo -e "  Stop services: ${GREEN}docker-compose -f $DOCKER_COMPOSE_FILE down${NC}"
    echo -e "  Restart service: ${GREEN}docker-compose -f $DOCKER_COMPOSE_FILE restart [service]${NC}"
    echo -e "  Check health: ${GREEN}docker-compose -f $DOCKER_COMPOSE_FILE ps --format 'table {{.Name}}\t{{.Status}}\t{{.Health}}'${NC}"
}

# Main execution
echo -e "${BLUE}🔍 Pre-deployment checks...${NC}"
check_docker
check_ports

echo ""
echo -e "${BLUE}🚀 Starting local development deployment...${NC}"

# Clean up if requested
if [[ "$CLEAN" == true ]]; then
    cleanup
fi

# Build images if requested
build_images

# Deploy services
deploy_services

# Wait for services if running in background
wait_for_services

# Show final status
show_status

echo ""
if [[ "$DETACH" == true ]]; then
    echo -e "${GREEN}🎉 Local development environment is running in the background!${NC}"
    echo -e "${BLUE}Use the commands above to manage your services${NC}"
else
    echo -e "${GREEN}🎉 Local development environment is running!${NC}"
    echo -e "${BLUE}Press Ctrl+C to stop all services${NC}"
fi
