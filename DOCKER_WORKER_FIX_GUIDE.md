# 🚨 Document-Worker RPC Error Fix Guide

## 🔍 **Problem Description**
```
target document-worker: failed to receive status: rpc error: code = Unavailable desc = error reading from server: unexpected EOF
```

This error typically occurs when the `document-worker` service fails to start or crashes during initialization.

## 🛠️ **Quick Fixes to Try**

### **1. Immediate Fix - Use Fixed Docker Compose File**
```bash
# Stop all services
docker-compose down -v

# Use the fixed version
docker-compose -f docker-compose.fixed.yml up -d --build
```

### **2. Check Docker Status**
```bash
# Restart Docker Desktop
open -a Docker

# Wait for Docker to fully start, then try again
docker-compose up -d --build
```

### **3. Step-by-Step Service Start**
```bash
# Start databases first
docker-compose up -d auth-db document-db indexing-db quiz-db notification-db redis minio

# Wait for databases to be healthy
sleep 30

# Start core services
docker-compose up -d auth-service
sleep 20
docker-compose up -d document-service
sleep 20
docker-compose up -d indexing-service
sleep 20

# Start workers last
docker-compose up -d document-worker indexing-worker quiz-worker
```

## 🔧 **Root Causes & Solutions**

### **Missing Environment Variables**
**Problem**: `document-worker` is missing critical environment variables
**Solution**: Add missing variables to the service:
```yaml
environment:
  # Add these to document-worker
  HUGGINGFACE_TOKEN: ${HUGGINGFACE_TOKEN:-}
  OPENAI_API_KEY: ${OPENAI_API_KEY:-}
```

### **Dependency Chain Issues**
**Problem**: Services start before dependencies are fully healthy
**Solution**: Use proper health checks:
```yaml
depends_on:
  document-service:
    condition: service_healthy  # ✅ Instead of service_started
```

### **Resource Constraints**
**Problem**: Insufficient memory/CPU for worker processes
**Solution**: Add resource limits and concurrency settings:
```yaml
command: celery -A app.celery_app worker --loglevel=info --queues=document_queue --concurrency=2
restart: unless-stopped
```

### **Network Issues**
**Problem**: Inter-service communication failures
**Solution**: Ensure proper network configuration and health checks

## 📋 **Troubleshooting Steps**

### **Step 1: Check Docker Status**
```bash
docker --version
docker-compose --version
docker info
```

### **Step 2: Clean Up**
```bash
# Stop and remove all containers
docker-compose down -v --remove-orphans

# Clean up Docker system
docker system prune -f

# Remove all images (optional, but recommended)
docker system prune -a -f
```

### **Step 3: Check Environment**
```bash
# Ensure .env.local exists
ls -la .env.local

# If not, create from example
cp env.local.example .env.local

# Update with your API keys
nano .env.local
```

### **Step 4: Start Fresh**
```bash
# Use the fixed compose file
docker-compose -f docker-compose.fixed.yml up -d --build
```

### **Step 5: Monitor Logs**
```bash
# Watch all services
docker-compose logs -f

# Watch specific service
docker-compose logs -f document-worker

# Check service status
docker-compose ps
```

## 🚀 **Prevention Measures**

### **1. Use Health Checks**
All services should have proper health checks before workers start.

### **2. Proper Dependencies**
Workers should wait for their dependencies to be healthy, not just started.

### **3. Resource Management**
Set appropriate concurrency limits and resource constraints.

### **4. Environment Validation**
Ensure all required environment variables are set with fallbacks.

## 🔍 **Debugging Commands**

### **Check Service Status**
```bash
docker-compose ps
docker-compose logs [service-name]
```

### **Check Network**
```bash
docker network ls
docker network inspect study-ai_study-ai-network
```

### **Check Resources**
```bash
docker stats
docker system df
```

### **Check Logs**
```bash
# Real-time logs
docker-compose logs -f document-worker

# Last 50 lines
docker-compose logs --tail=50 document-worker

# Since specific time
docker-compose logs --since="2024-01-01T00:00:00" document-worker
```

## 📞 **If All Else Fails**

### **1. Restart Docker Desktop**
- Quit Docker Desktop completely
- Wait 10 seconds
- Restart Docker Desktop
- Wait for full startup

### **2. Reset Docker**
```bash
# Reset Docker to factory defaults (⚠️ This will remove all containers/images)
# Only do this if nothing else works
```

### **3. Check System Resources**
- Ensure sufficient RAM (at least 8GB available)
- Check disk space (at least 10GB free)
- Monitor CPU usage

### **4. Alternative Approach**
```bash
# Start only essential services first
docker-compose up -d auth-db document-db redis minio

# Wait for health
sleep 30

# Start services one by one
docker-compose up -d auth-service
docker-compose up -d document-service
docker-compose up -d document-worker
```

## 🎯 **Success Indicators**

When working correctly, you should see:
- All services show `healthy` status
- Workers show `Up` status
- No RPC errors in logs
- Successful Celery worker startup messages

## 📚 **Additional Resources**

- [Docker Compose Health Checks](https://docs.docker.com/compose/compose-file/compose-file-v3/#healthcheck)
- [Celery Worker Configuration](https://docs.celeryproject.org/en/stable/userguide/workers.html)
- [Docker Network Troubleshooting](https://docs.docker.com/network/troubleshooting/)

---

**Remember**: The key is to start services in the correct order with proper health checks, and ensure all dependencies are fully ready before starting workers.
