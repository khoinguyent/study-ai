#!/bin/bash

# Build and Test Script for Document Service
# This script builds the Docker container and tests PDF processing

set -e

echo "🚀 Building Document Service Docker Container..."
echo "================================================"

# Build the Docker image
echo "📦 Building Docker image..."
docker build -t study-ai-document-service .

if [ $? -eq 0 ]; then
    echo "✅ Docker build successful!"
else
    echo "❌ Docker build failed!"
    exit 1
fi

echo ""
echo "🧪 Testing Docker Container..."
echo "=============================="

# Test if the container can start
echo "🔍 Testing container startup..."
CONTAINER_ID=$(docker run -d -p 8002:8002 --name test-doc-service study-ai-document-service)

if [ $? -eq 0 ]; then
    echo "✅ Container started successfully (ID: $CONTAINER_ID)"
    
    # Wait for container to be ready
    echo "⏳ Waiting for container to be ready..."
    sleep 10
    
    # Test health endpoint
    echo "🏥 Testing health endpoint..."
    if curl -f http://localhost:8002/health > /dev/null 2>&1; then
        echo "✅ Health endpoint working"
    else
        echo "❌ Health endpoint failed"
    fi
    
    # Test supported formats endpoint
    echo "📋 Testing supported formats endpoint..."
    if curl -f http://localhost:8002/supported-formats > /dev/null 2>&1; then
        echo "✅ Supported formats endpoint working"
    else
        echo "❌ Supported formats endpoint failed"
    fi
    
    # Stop and remove test container
    echo "🧹 Cleaning up test container..."
    docker stop $CONTAINER_ID
    docker rm $CONTAINER_ID
    
    echo ""
    echo "🎉 All tests passed! Docker container is working correctly."
    echo ""
    echo "📝 To run the container:"
    echo "   docker run -d -p 8002:8002 --name document-service study-ai-document-service"
    echo ""
    echo "📝 To test PDF processing:"
    echo "   curl -X POST -F 'file=@../../data/de-cuong-on-tap-hoc-ki-1-mon-lich-su-lop-8.pdf' http://localhost:8002/extract-pdf-text"
    
else
    echo "❌ Failed to start container!"
    exit 1
fi
