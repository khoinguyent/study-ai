#!/bin/bash

# Fix Quiz Worker RPC Error Script
# This script specifically addresses the "target quiz-worker: failed to receive status: rpc error: code = Unavailable desc = error reading from server: unexpected EOF" error

set -e

echo "🔧 Fixing Quiz Worker RPC Error..."

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker is not running. Please start Docker Desktop and try again."
    exit 1
fi

echo "✅ Docker is running"

# Stop the quiz-worker specifically
echo "🛑 Stopping quiz-worker..."
docker-compose stop quiz-worker || true

# Remove the quiz-worker container
echo "🗑️  Removing quiz-worker container..."
docker-compose rm -f quiz-worker || true

# Clean up any dangling quiz-worker images
echo "🧹 Cleaning up quiz-worker images..."
docker image prune -f || true

# Rebuild the quiz-service (which includes the worker)
echo "🔨 Rebuilding quiz-service..."
docker-compose build --no-cache quiz-service

# Start the quiz-worker with proper environment
echo "🚀 Starting quiz-worker..."
docker-compose up -d quiz-worker

# Wait for the worker to start
echo "⏳ Waiting for quiz-worker to start..."
sleep 15

# Check the worker logs
echo "📋 Checking quiz-worker logs..."
docker-compose logs quiz-worker --tail=20

echo ""
echo "✅ Quiz Worker RPC error should be fixed!"
echo "📋 To monitor logs: docker-compose logs -f quiz-worker"
echo "🔄 To restart: docker-compose restart quiz-worker"
