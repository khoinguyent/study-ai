#!/bin/bash
# Study AI Application Deployment Script
# This script deploys your application to the EC2 instance

set -e

echo "🚀 Starting Study AI Application Deployment..."

# Configuration
APP_NAME="studyai-app"
APP_PORT=3000
DOCKER_IMAGE="your-registry/studyai-app:latest"  # Update this with your actual image
S3_BUCKET="studyai-uploads-dev-ap-southeast-1"
AWS_REGION="ap-southeast-1"

echo "📋 Configuration:"
echo "  App Name: $APP_NAME"
echo "  Port: $APP_PORT"
echo "  Docker Image: $DOCKER_IMAGE"
echo "  S3 Bucket: $S3_BUCKET"
echo "  AWS Region: $AWS_REGION"

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker is not running. Starting Docker..."
    sudo systemctl start docker
    sudo systemctl enable docker
fi

# Stop and remove existing container if it exists
if docker ps -a --format "table {{.Names}}" | grep -q "^$APP_NAME$"; then
    echo "🔄 Stopping existing container..."
    docker stop $APP_NAME
    docker rm $APP_NAME
fi

# Pull latest image
echo "📥 Pulling latest Docker image..."
docker pull $DOCKER_IMAGE

# Run the application
echo "🚀 Starting application container..."
docker run -d \
    --name $APP_NAME \
    --restart unless-stopped \
    -p $APP_PORT:$APP_PORT \
    -e NODE_ENV=production \
    -e AWS_REGION=$AWS_REGION \
    -e S3_BUCKET=$S3_BUCKET \
    -e PORT=$APP_PORT \
    $DOCKER_IMAGE

# Wait for container to start
echo "⏳ Waiting for container to start..."
sleep 10

# Check container status
if docker ps --format "table {{.Names}}\t{{.Status}}" | grep -q "$APP_NAME.*Up"; then
    echo "✅ Container is running successfully!"
    
    # Test the application
    echo "🧪 Testing application..."
    if curl -s http://localhost:$APP_PORT > /dev/null; then
        echo "✅ Application is responding on port $APP_PORT"
    else
        echo "⚠️  Application is not responding on port $APP_PORT"
    fi
    
    # Show container logs
    echo "📋 Container logs:"
    docker logs $APP_NAME --tail 20
    
else
    echo "❌ Container failed to start. Checking logs..."
    docker logs $APP_NAME
    exit 1
fi

echo "🎉 Deployment completed successfully!"
echo "🌐 Your application should be accessible at: http://$(curl -s http://169.254.169.254/latest/meta-data/public-ipv4)"
echo "📊 Container status:"
docker ps --filter "name=$APP_NAME"
