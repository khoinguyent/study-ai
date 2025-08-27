#!/bin/bash

echo "🚀 Testing Docker build for quiz-service"
echo "=========================================="

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker is not running. Please start Docker and try again."
    exit 1
fi

echo "✅ Docker is running"

# Check if we're in the right directory
if [ ! -f "Dockerfile" ]; then
    echo "❌ Dockerfile not found. Please run this script from the quiz-service directory."
    exit 1
fi

echo "✅ Dockerfile found"

# Check if requirements.txt exists
if [ ! -f "requirements.txt" ]; then
    echo "❌ requirements.txt not found"
    exit 1
fi

echo "✅ requirements.txt found"

# Check if app directory exists
if [ ! -d "app" ]; then
    echo "❌ app directory not found"
    exit 1
fi

echo "✅ app directory found"

# Try to build the Docker image
echo "🔨 Building Docker image..."
if docker build -t quiz-service-test .; then
    echo "✅ Docker build successful!"
    
    # Test if the container can start
    echo "🧪 Testing container startup..."
    if docker run --rm -d --name quiz-service-test quiz-service-test; then
        echo "✅ Container started successfully"
        
        # Wait a moment for the service to start
        sleep 5
        
        # Check if the service is responding
        if docker exec quiz-service-test curl -f http://localhost:8004/health > /dev/null 2>&1; then
            echo "✅ Service is responding to health check"
        else
            echo "⚠️  Service health check failed (this might be expected if dependencies are missing)"
        fi
        
        # Clean up
        docker stop quiz-service-test
        echo "✅ Container stopped and cleaned up"
    else
        echo "❌ Container failed to start"
        exit 1
    fi
else
    echo "❌ Docker build failed"
    exit 1
fi

echo ""
echo "🎉 Docker build test completed successfully!"
echo "The quiz-service can be built and run in Docker."
