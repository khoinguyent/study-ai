# 🚀 Workflow Quick Reference Card

## 🏠 **Local Development**

### **Start Local Environment**
```bash
# Start all services
./scripts/deploy-local.sh -d

# Start specific service
./scripts/deploy-local.sh -s api-gateway -d

# Force rebuild
./scripts/deploy-local.sh -b -d

# Clean start
./scripts/deploy-local.sh -c -d
```

### **Local Service URLs**
- **Web UI**: http://localhost:3000
- **API Gateway**: http://localhost:8000
- **Auth Service**: http://localhost:8001
- **Document Service**: http://localhost:8002
- **Indexing Service**: http://localhost:8003
- **Quiz Service**: http://localhost:8004
- **Notification Service**: http://localhost:8005
- **Leaf Quiz Service**: http://localhost:8006

### **Local Management**
```bash
# View status
docker-compose ps

# View logs
docker-compose logs -f [service-name]

# Restart service
docker-compose restart [service-name]

# Stop all
docker-compose down

# Clean up
docker-compose down --volumes --remove-orphans
```

## 🔄 **Feature Development Workflow**

### **1. Create Feature Branch**
```bash
git checkout -b feature/your-feature-name
```

### **2. Develop and Test Locally**
```bash
# Start local environment
./scripts/deploy-local.sh -d

# Make your changes
# Test locally
curl http://localhost:8000/health

# Stop when done
docker-compose down
```

### **3. Commit and Push**
```bash
git add .
git commit -m "feat: your feature description"
git push origin feature/your-feature-name
```

### **4. Create Pull Request**
- Go to GitHub repository
- Click "Compare & pull request"
- Set base branch to `develop`
- Add description and reviewers
- **CI/CD automatically triggers**

## ☁️ **Staging Environment**

### **Deploy to Staging**
```bash
# Deploy to staging (develop branch)
./scripts/deploy-ci-cd.sh -e staging -t rolling

# Check status
docker-compose -f docker-compose.cloud.yml ps

# View logs
docker-compose -f docker-compose.cloud.yml logs -f
```

### **Staging Validation Checklist**
- [ ] All services healthy
- [ ] Database connections work
- [ ] S3 uploads work
- [ ] Redis caching works
- [ ] SQS processing works
- [ ] API endpoints respond
- [ ] Frontend loads
- [ ] Performance acceptable

## 🚀 **Production Deployment**

### **Deploy to Production**
```bash
# After staging validation, merge to main
git checkout develop
git pull origin develop
git checkout main
git merge develop
git push origin main

# Monitor deployment
./scripts/deploy-ci-cd.sh -e production -t blue-green
```

### **Production Monitoring**
```bash
# Check status
docker-compose -f docker-compose.cloud.yml ps

# Monitor logs
docker-compose -f docker-compose.cloud.yml logs -f

# Health checks
curl https://api.yourdomain.com/health
```

## 🔧 **Environment Comparison**

| Environment | Infrastructure | Database | Cache | Storage | LLM | Purpose |
|-------------|----------------|----------|-------|---------|-----|---------|
| **Local** | Docker Compose | Local PostgreSQL | Local Redis | Local MinIO | Local Ollama | Development |
| **Staging** | AWS Cloud | EC2 PostgreSQL | ElastiCache | S3 | SageMaker | Testing |
| **Production** | AWS Cloud | EC2 PostgreSQL | ElastiCache | S3 | SageMaker | Live Users |

## 📋 **Daily Commands**

### **Morning Routine**
```bash
# Start local development
./scripts/deploy-local.sh -d

# Check all services are running
docker-compose ps
```

### **Development Session**
```bash
# Make changes to code
# Test locally
curl http://localhost:8000/health

# View logs if issues
docker-compose logs -f [service-name]
```

### **End of Day**
```bash
# Stop local environment
docker-compose down

# Commit changes if ready
git add . && git commit -m "feat: your changes"
```

## 🚨 **Troubleshooting**

### **Common Issues**

#### **Port Conflicts**
```bash
# Check what's using a port
lsof -i :8000

# Kill process on port
lsof -ti:8000 | xargs kill -9
```

#### **Service Not Starting**
```bash
# Check logs
docker-compose logs [service-name]

# Check health status
docker-compose ps --format "table {{.Name}}\t{{.Status}}\t{{.Health}}"
```

#### **Database Issues**
```bash
# Check database health
docker exec study-ai-auth-db pg_isready -U postgres

# Restart database
docker-compose restart auth-db
```

### **Reset Everything**
```bash
# Nuclear option - clean everything
docker-compose down --volumes --remove-orphans
docker system prune -af
./scripts/deploy-local.sh -c -d
```

## 🎯 **Quick Commands Reference**

| Action | Command |
|--------|---------|
| **Start Local** | `./scripts/deploy-local.sh -d` |
| **Stop Local** | `docker-compose down` |
| **View Status** | `docker-compose ps` |
| **View Logs** | `docker-compose logs -f [service]` |
| **Restart Service** | `docker-compose restart [service]` |
| **Deploy Staging** | `./scripts/deploy-ci-cd.sh -e staging` |
| **Deploy Production** | `./scripts/deploy-ci-cd.sh -e production` |
| **Check Health** | `curl http://localhost:8000/health` |

## 📚 **Documentation Links**

- **Full Workflow**: `MULTI_ENVIRONMENT_WORKFLOW.md`
- **CI/CD Guide**: `CI_CD_GUIDE.md`
- **Cloud Deployment**: `CLOUD_DEPLOYMENT_WORKFLOW.md`
- **Infrastructure**: `INFRASTRUCTURE_ARCHITECTURE.md`

---

**Remember**: Always test locally first, then staging, then production! 🚀
