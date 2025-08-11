# 🚀 Multi-Environment CI/CD Workflow: Local → Staging → Production

## 🎯 **Overview**

This guide explains the complete workflow for developing, testing, and deploying the Study AI Platform across multiple environments:

- **🏠 Local Development**: Docker Compose with local infrastructure
- **☁️ Staging**: Cloud infrastructure for testing and validation
- **🚀 Production**: Cloud infrastructure for live users

## 🌿 **Branching Strategy Setup**

### **Required Branch Structure**
Before using this workflow, you need to set up the proper branching strategy:

```bash
# Setup branching strategy (run once)
./scripts/setup-branches.sh
```

This creates:
```
main (production)
├── develop (staging)
    ├── feature/your-feature (development)
    ├── feature/another-feature
    └── hotfix/urgent-fix
```

### **Branch Protection Rules**
The setup script also configures:
- **main branch**: Protected, requires PR reviews and CI/CD checks
- **develop branch**: Protected, requires PR reviews and CI/CD checks
- **feature branches**: Unprotected, for development

### **Environment Mapping**
- **feature/* branches** → Local development
- **develop branch** → Staging environment (cloud)
- **main branch** → Production environment (cloud)

## 🏗️ **Environment Architecture**

### **Local Development Environment**
```
┌─────────────────────────────────────────────────────────────┐
│                    Local Machine                           │
├─────────────────────────────────────────────────────────────┤
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐        │
│  │   Web UI    │  │ API Gateway │  │ Auth Service│        │
│  │  (Port 3000)│  │ (Port 8000) │  │(Port 8001) │        │
│  └─────────────┘  └─────────────┘  └─────────────┘        │
│                                                           │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐        │
│  │Document Svc │  │Indexing Svc │  │ Quiz Service│        │
│  │(Port 8002)  │  │(Port 8003)  │  │(Port 8004) │        │
│  └─────────────┘  └─────────────┘  └─────────────┘        │
│                                                           │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐        │
│  │Notification │  │Leaf Quiz    │  │ PostgreSQL  │        │
│  │(Port 8005)  │  │(Port 8006)  │  │(Ports 5432+)│        │
│  └─────────────┘  └─────────────┘  └─────────────┘        │
│                                                           │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐        │
│  │   Redis     │  │   MinIO     │  │   Ollama    │        │
│  │(Port 6379)  │  │(Port 9000)  │  │(Port 11434)│        │
│  └─────────────┘  └─────────────┘  └─────────────┘        │
└─────────────────────────────────────────────────────────────┘
```

### **Cloud Staging/Production Environment**
```
┌─────────────────────────────────────────────────────────────┐
│                    AWS Cloud                               │
├─────────────────────────────────────────────────────────────┤
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐        │
│  │   Web UI    │  │ API Gateway │  │ Auth Service│        │
│  │  (Port 3000)│  │ (Port 8000) │  │(Port 8001) │        │
│  └─────────────┘  └─────────────┘  └─────────────┘        │
│                                                           │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐        │
│  │Document Svc │  │Indexing Svc │  │ Quiz Service│        │
│  │(Port 8002)  │  │(Port 8003)  │  │(Port 8004) │        │
│  └─────────────┘  └─────────────┘  └─────────────┘        │
│                                                           │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐        │
│  │Notification │  │Leaf Quiz    │  │ PostgreSQL  │        │
│  │(Port 8005)  │  │(Port 8006)  │  │(Port 5432+)│        │
│  └─────────────┘  └─────────────┘  └─────────────┘        │
│                                                           │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐        │
│  │ ElastiCache │  │     S3      │  │  SageMaker  │        │
│  │   (Redis)   │  │ (Storage)   │  │   (LLM)    │        │
│  └─────────────┘  └─────────────┘  └─────────────┘        │
└─────────────────────────────────────────────────────────────┘
```

## 🔄 **Complete Development Workflow**

### **Phase 1: Setup Branching Strategy 🌿**

#### **1.1 Initial Setup (Run Once)**
```bash
# Setup proper branching strategy
./scripts/setup-branches.sh

# This creates:
# - develop branch (staging)
# - Branch protection rules
# - Example feature branch
```

#### **1.2 Verify Branch Structure**
```bash
# Check your branches
git branch -a

# You should see:
# - main (production)
# - develop (staging)
# - feature/example-feature (development)
```

### **Phase 2: Local Development 🏠**

#### **2.1 Start Local Environment**
```bash
# Start all services locally
./scripts/deploy-local.sh -d

# Or start specific service
./scripts/deploy-local.sh -s api-gateway -d

# Force rebuild if needed
./scripts/deploy-local.sh -b -d

# Clean start
./scripts/deploy-local.sh -c -d
```

#### **2.2 Develop and Test Locally**
```bash
# Your local services are now running at:
# Web UI: http://localhost:3000
# API Gateway: http://localhost:8000
# Auth Service: http://localhost:8001
# Document Service: http://localhost:8002
# Indexing Service: http://localhost:8003
# Quiz Service: http://localhost:8004
# Notification Service: http://localhost:8005
# Leaf Quiz Service: http://localhost:8006

# Test your changes locally
curl http://localhost:8000/health
curl http://localhost:8002/health
```

#### **2.3 Local Development Commands**
```bash
# View service status
docker-compose ps

# View logs
docker-compose logs -f [service-name]

# Restart service
docker-compose restart [service-name]

# Stop all services
docker-compose down

# Clean up completely
docker-compose down --volumes --remove-orphans
```

### **Phase 3: Feature Development 🚀**

#### **3.1 Create Feature Branch**
```bash
# Always start from develop branch
git checkout develop
git pull origin develop

# Create feature branch
git checkout -b feature/new-quiz-type

# Make your changes
# Test locally with ./scripts/deploy-local.sh
```

#### **3.2 Commit and Push**
```bash
# Commit your changes
git add .
git commit -m "feat: add new quiz type with enhanced scoring"

# Push feature branch
git push origin feature/new-quiz-type
```

#### **3.3 Create Pull Request**
1. Go to GitHub repository
2. Click "Compare & pull request"
3. **Important**: Set base branch to `develop` (not main)
4. Add description and reviewers
5. **CI/CD Pipeline Automatically Triggers**

### **Phase 4: CI/CD Pipeline Execution 🔄**

#### **4.1 Automated Testing (GitHub Actions)**
```yaml
# What happens automatically:
1. Code Quality Check
   - Python linting (flake8, black, isort)
   - TypeScript linting (ESLint)
   - Unit tests with coverage

2. Docker Image Builds
   - Build all service images
   - Push to GitHub Container Registry
   - Cache layers for faster builds

3. Integration Testing
   - Full-stack testing with test databases
   - Service communication validation
   - API endpoint testing

4. Security Scanning
   - Trivy vulnerability scanner
   - Snyk dependency analysis
   - Container security checks
```

#### **4.2 Staging Deployment (develop branch)**
```yaml
# After PR is merged to develop:
1. Automatic deployment to staging environment
2. Run smoke tests
3. Validate cloud infrastructure
4. Test with real AWS services
```

### **Phase 5: Staging Validation ☁️**

#### **5.1 Access Staging Environment**
```bash
# Staging URLs (configured in env.cloud)
# Web UI: https://staging.yourdomain.com
# API Gateway: https://staging-api.yourdomain.com

# Test staging deployment
curl https://staging-api.yourdomain.com/health
```

#### **5.2 Staging Testing**
```bash
# Run comprehensive tests on staging
./scripts/deploy-ci-cd.sh -e staging -t rolling

# Test with real data
# - Upload documents to S3
# - Test ElastiCache Redis
# - Test SQS message queues
# - Test EC2 PostgreSQL
```

#### **5.3 Staging Validation Checklist**
- [ ] All services are healthy
- [ ] Database connections work
- [ ] File uploads to S3 work
- [ ] Redis caching works
- [ ] SQS message processing works
- [ ] API endpoints respond correctly
- [ ] Frontend loads and functions
- [ ] Performance is acceptable

### **Phase 6: Production Deployment 🚀**

#### **6.1 Merge to Main Branch**
```bash
# After staging validation, merge develop to main
git checkout develop
git pull origin develop

git checkout main
git pull origin main

# Merge develop into main
git merge develop

# Push to main (triggers production deployment)
git push origin main
```

#### **6.2 Production Deployment Process**
```yaml
# Production deployment (main branch):
1. Automated deployment to production
2. Blue-green deployment strategy
3. Health checks and smoke tests
4. Performance monitoring
5. Rollback capability if issues detected
```

#### **6.3 Production Validation**
```bash
# Production URLs
# Web UI: https://yourdomain.com
# API Gateway: https://api.yourdomain.com

# Production health check
curl https://api.yourdomain.com/health

# Monitor production deployment
./scripts/deploy-ci-cd.sh -e production -t blue-green
```

## 📋 **Step-by-Step Workflow Example**

### **Scenario: Adding a New Quiz Type**

#### **Step 1: Setup (Run Once)**
```bash
# Setup branching strategy
./scripts/setup-branches.sh
```

#### **Step 2: Local Development**
```bash
# 1. Start local environment
./scripts/deploy-local.sh -d

# 2. Create feature branch from develop
git checkout develop
git pull origin develop
git checkout -b feature/advanced-quiz

# 3. Make changes to quiz service
# Edit: services/quiz-service/app/services/quiz_generator.py
# Add new quiz type logic

# 4. Test locally
curl http://localhost:8004/health
# Test new quiz generation endpoint

# 5. Stop local environment
docker-compose down
```

#### **Step 3: Commit and Push**
```bash
# 6. Commit changes
git add .
git commit -m "feat: add advanced quiz type with adaptive difficulty"

# 7. Push to remote
git push origin feature/advanced-quiz
```

#### **Step 4: Create Pull Request**
```bash
# 8. Create PR from feature/advanced-quiz to develop
# GitHub Actions automatically:
# - Runs tests
# - Builds Docker images
# - Deploys to staging
```

#### **Step 5: Staging Validation**
```bash
# 9. Test on staging
# - Verify new quiz type works
# - Test with real cloud infrastructure
# - Validate performance

# 10. Get team approval
# - Code review
# - Staging testing approval
```

#### **Step 6: Production Deployment**
```bash
# 11. Merge to develop (PR approval)
# - Automatically deploys to staging

# 12. Merge to main (production)
git checkout main
git merge develop
git push origin main

# 13. Monitor production deployment
# - Check GitHub Actions
# - Verify production health
# - Monitor for any issues
```

## 🔧 **Environment-Specific Commands**

### **Local Development**
```bash
# Start local environment
./scripts/deploy-local.sh -d

# Stop local environment
docker-compose down

# View local logs
docker-compose logs -f [service-name]

# Restart local service
docker-compose restart [service-name]
```

### **Staging Environment**
```bash
# Deploy to staging
./scripts/deploy-ci-cd.sh -e staging -t rolling

# Check staging status
docker-compose -f docker-compose.cloud.yml ps

# View staging logs
docker-compose -f docker-compose.cloud.yml logs -f
```

### **Production Environment**
```bash
# Deploy to production
./scripts/deploy-ci-cd.sh -e production -t blue-green

# Check production status
docker-compose -f docker-compose.cloud.yml ps

# Monitor production
docker-compose -f docker-compose.cloud.yml logs -f
```

## 📊 **Environment Comparison**

| Environment | Infrastructure | Database | Cache | Storage | LLM | Purpose |
|-------------|----------------|----------|-------|---------|-----|---------|
| **Local** | Docker Compose | Local PostgreSQL | Local Redis | Local MinIO | Local Ollama | Development |
| **Staging** | AWS Cloud | EC2 PostgreSQL | ElastiCache | S3 | SageMaker | Testing |
| **Production** | AWS Cloud | EC2 PostgreSQL | ElastiCache | S3 | SageMaker | Live Users |

## 🚨 **Best Practices**

### **Development Workflow**
- ✅ **Always test locally first** before pushing
- ✅ **Create feature branches from develop** (not main)
- ✅ **Test on staging** before production
- ✅ **Monitor deployments** for any issues
- ✅ **Use descriptive commit messages**

### **Branching Strategy**
- ✅ **Never commit directly to main** (use PRs)
- ✅ **Never commit directly to develop** (use PRs)
- ✅ **Create feature branches from develop**
- ✅ **Merge develop to main** for production releases
- ✅ **Use hotfix branches** for urgent production fixes

### **Environment Management**
- ✅ **Keep environments similar** (local vs cloud)
- ✅ **Use environment-specific configs** (env.local, env.cloud)
- ✅ **Test cloud features** on staging
- ✅ **Validate infrastructure** before production
- ✅ **Monitor resource usage** in cloud

### **Deployment Safety**
- ✅ **Use rolling deployments** for zero downtime
- ✅ **Implement health checks** for all services
- ✅ **Run smoke tests** after deployment
- ✅ **Have rollback strategy** ready
- ✅ **Monitor logs** during deployment

## 🎯 **Quick Reference Commands**

### **Daily Development**
```bash
# Start local environment
./scripts/deploy-local.sh -d

# Make changes and test locally
# Stop when done
docker-compose down
```

### **Feature Development**
```bash
# Create feature branch
git checkout develop && git pull origin develop
git checkout -b feature/your-feature

# Develop and test locally
./scripts/deploy-local.sh -d

# Commit and push
git add . && git commit -m "feat: your feature"
git push origin feature/your-feature

# Create PR to develop
```

### **Deployment**
```bash
# Deploy to staging (after PR merge to develop)
./scripts/deploy-ci-cd.sh -e staging -t rolling

# Deploy to production (after merge to main)
git checkout main && git merge develop && git push origin main
```

## 🚨 **Common Mistakes to Avoid**

### **❌ Wrong Branch Merging**
```bash
# DON'T do this:
git checkout main
git merge feature/your-feature  # Wrong! Merge to develop first

# DO this instead:
git checkout develop
git merge feature/your-feature  # Correct! Merge to develop first
git checkout main
git merge develop               # Then merge develop to main
```

### **❌ Skipping Staging**
```bash
# DON'T skip staging validation
# Always test on staging before production

# DO use the proper flow:
# feature → develop (staging) → main (production)
```

### **❌ Direct Commits to Protected Branches**
```bash
# DON'T commit directly to main or develop
# Use feature branches and pull requests instead
```

This workflow ensures **safe, reliable deployments** from local development to production, with **automated testing** and **staging validation** at every step! 🚀
