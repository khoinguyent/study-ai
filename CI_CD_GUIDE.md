# 🚀 CI/CD Guide - Study AI Platform

## 🎯 **Overview**

This guide explains how to implement Continuous Integration and Continuous Deployment (CI/CD) for your Study AI Platform. We'll cover multiple approaches and provide step-by-step setup instructions.

## 🏗️ **CI/CD Architecture Options**

### **Option 1: GitHub Actions (Recommended) ⭐**
- **Pros**: Free for public repos, easy setup, great GitHub integration
- **Cons**: Limited build minutes for private repos
- **Best for**: Small to medium teams, GitHub-based workflows

### **Option 2: AWS CodePipeline + CodeBuild**
- **Pros**: Native AWS integration, scalable, cost-effective
- **Cons**: More complex setup, AWS-specific
- **Best for**: AWS-heavy environments, enterprise teams

### **Option 3: GitLab CI/CD**
- **Pros**: Free, integrated with GitLab, powerful features
- **Cons**: Requires GitLab hosting
- **Best for**: GitLab users, self-hosted environments

### **Option 4: Jenkins**
- **Pros**: Highly customizable, extensive plugin ecosystem
- **Cons**: Complex setup, requires server maintenance
- **Best for**: Large teams, complex deployment requirements

---

## 🎯 **Option 1: GitHub Actions (Recommended)**

### **🚀 Quick Start**

#### **1.1 Enable GitHub Actions**
1. Go to your GitHub repository
2. Click **Actions** tab
3. Click **New workflow**
4. Choose **Skip this and set up a workflow yourself**

#### **1.2 Set Up Repository Secrets**
Go to **Settings** → **Secrets and variables** → **Actions** and add:

```bash
# AWS Staging Environment
AWS_ACCESS_KEY_ID_STAGING=your-staging-access-key
AWS_SECRET_ACCESS_KEY_STAGING=your-staging-secret-key
AWS_REGION_STAGING=us-east-1

# AWS Production Environment
AWS_ACCESS_KEY_ID_PROD=your-production-access-key
AWS_SECRET_ACCESS_KEY_PROD=your-production-secret-key
AWS_REGION_PROD=us-east-1

# Security Scanning
SNYK_TOKEN=your-snyk-token
```

#### **1.3 Create Environments**
Go to **Settings** → **Environments** and create:

**Staging Environment:**
- Name: `staging`
- Protection rules: `Required reviewers` (optional)

**Production Environment:**
- Name: `production`
- Protection rules: `Required reviewers` (recommended)

### **🔧 Workflow Features**

#### **Code Quality & Testing**
- ✅ Python linting (flake8, black, isort)
- ✅ TypeScript linting (ESLint)
- ✅ Unit tests with coverage
- ✅ Integration tests
- ✅ Security scanning (Trivy, Snyk)

#### **Docker Build & Push**
- ✅ Multi-service matrix builds
- ✅ GitHub Container Registry integration
- ✅ Layer caching for faster builds
- ✅ Automatic tagging (branch, PR, release)

#### **Deployment Strategies**
- ✅ Rolling deployment
- ✅ Blue-green deployment
- ✅ Canary deployment
- ✅ Environment-specific configurations

#### **Monitoring & Notifications**
- ✅ Health checks
- ✅ Smoke tests
- ✅ Performance testing
- ✅ Deployment notifications

### **📋 Workflow Triggers**

```yaml
on:
  push:
    branches: [ main, develop, feature/* ]
  pull_request:
    branches: [ main, develop ]
  release:
    types: [published]
```

### **🔄 Deployment Flow**

1. **Code Push** → **Code Quality** → **Build Images** → **Integration Tests**
2. **Develop Branch** → **Deploy to Staging**
3. **Main Branch** → **Deploy to Production**
4. **Release Tag** → **Deploy to Production**

---

## 🎯 **Option 2: AWS CodePipeline + CodeBuild**

### **🚀 Setup Instructions**

#### **2.1 Create CodeBuild Project**
```bash
# Create buildspec.yml in your repository
aws codebuild create-project \
  --project-name study-ai-build \
  --source type=GITHUB,location=https://github.com/your-username/study-ai \
  --artifacts type=NO_ARTIFACTS \
  --environment type=LINUX_CONTAINER,image=aws/codebuild/amazonlinux2-x86_64-standard:4.0
```

#### **2.2 Create buildspec.yml**
```yaml
version: 0.2

phases:
  install:
    runtime-versions:
      python: 3.11
      nodejs: 18
    commands:
      - pip install --upgrade pip
      - pip install -r services/api-gateway/requirements.txt
      
  pre_build:
    commands:
      - echo Logging in to Amazon ECR...
      - aws --version
      
  build:
    commands:
      - echo Build started on `date`
      - docker build -t study-ai-api-gateway ./services/api-gateway
      
  post_build:
    commands:
      - echo Build completed on `date`
```

#### **2.3 Create CodePipeline**
```bash
aws codepipeline create-pipeline \
  --pipeline-name study-ai-pipeline \
  --pipeline-definition file://pipeline-definition.json
```

### **🔧 Pipeline Stages**

1. **Source**: GitHub source code
2. **Build**: CodeBuild compilation
3. **Deploy**: ECS/EC2 deployment
4. **Test**: Automated testing
5. **Approval**: Manual approval (production)

---

## 🎯 **Option 3: GitLab CI/CD**

### **🚀 Setup Instructions**

#### **3.1 Create .gitlab-ci.yml**
```yaml
stages:
  - test
  - build
  - deploy

variables:
  DOCKER_DRIVER: overlay2
  DOCKER_TLS_CERTDIR: "/certs"

before_script:
  - docker login -u $CI_REGISTRY_USER -p $CI_REGISTRY_PASSWORD $CI_REGISTRY

test:
  stage: test
  image: python:3.11
  script:
    - pip install -r services/api-gateway/requirements.txt
    - python -m pytest services/

build:
  stage: build
  image: docker:latest
  services:
    - docker:dind
  script:
    - docker build -t $CI_REGISTRY_IMAGE:$CI_COMMIT_SHA ./services/api-gateway
    - docker push $CI_REGISTRY_IMAGE:$CI_COMMIT_SHA

deploy:
  stage: deploy
  image: alpine:latest
  script:
    - apk add --no-cache curl
    - curl -X POST $DEPLOY_WEBHOOK
  only:
    - main
```

---

## 🎯 **Option 4: Jenkins**

### **🚀 Setup Instructions**

#### **4.1 Install Jenkins**
```bash
# Ubuntu/Debian
wget -q -O - https://pkg.jenkins.io/debian-stable/jenkins.io-2023.key | sudo apt-key add -
sudo sh -c 'echo deb https://pkg.jenkins.io/debian-stable binary/ > /etc/apt/sources.list.d/jenkins.list'
sudo apt-get update
sudo apt-get install jenkins

# Start Jenkins
sudo systemctl start jenkins
sudo systemctl enable jenkins
```

#### **4.2 Create Jenkinsfile**
```groovy
pipeline {
    agent any
    
    stages {
        stage('Checkout') {
            steps {
                checkout scm
            }
        }
        
        stage('Test') {
            steps {
                sh 'pip install -r services/api-gateway/requirements.txt'
                sh 'python -m pytest services/'
            }
        }
        
        stage('Build') {
            steps {
                sh 'docker build -t study-ai-api-gateway ./services/api-gateway'
            }
        }
        
        stage('Deploy') {
            steps {
                sh './scripts/deploy-ci-cd.sh -e production -t rolling'
            }
        }
    }
}
```

---

## 🔧 **Deployment Strategies**

### **🔄 Rolling Deployment**
- **How it works**: Updates services one by one
- **Pros**: Zero downtime, easy rollback
- **Cons**: Temporary version mismatch
- **Best for**: Most applications

### **🔵🟢 Blue-Green Deployment**
- **How it works**: Deploy new version alongside old, switch traffic
- **Pros**: Zero downtime, instant rollback
- **Cons**: Requires double resources
- **Best for**: Critical applications

### **🐦 Canary Deployment**
- **How it works**: Deploy to subset of users first
- **Pros**: Risk mitigation, gradual rollout
- **Cons**: Complex traffic management
- **Best for**: High-risk changes

---

## 📊 **Monitoring & Observability**

### **Health Checks**
```yaml
# Docker Compose health checks
healthcheck:
  test: ["CMD-SHELL", "pg_isready -U postgres"]
  interval: 10s
  timeout: 5s
  retries: 5
```

### **Smoke Tests**
```bash
# Test API endpoints
curl -f http://localhost:8000/health
curl -f http://localhost:3000

# Test database connections
docker exec study-ai-auth-db pg_isready -U postgres
```

### **Performance Testing**
```bash
# Install Locust
pip install locust

# Run load tests
locust -f tests/performance/locustfile.py --host=http://localhost:8000
```

---

## 🔐 **Security Best Practices**

### **Secrets Management**
- ✅ Use GitHub Secrets (not hardcoded)
- ✅ Rotate credentials regularly
- ✅ Least privilege access
- ✅ Environment-specific secrets

### **Container Security**
- ✅ Scan images for vulnerabilities
- ✅ Use minimal base images
- ✅ Regular security updates
- ✅ Non-root user execution

### **Network Security**
- ✅ Private subnets for databases
- ✅ Security groups with minimal access
- ✅ VPC endpoints for AWS services
- ✅ SSL/TLS encryption

---

## 📈 **Performance Optimization**

### **Build Optimization**
```yaml
# Docker layer caching
cache-from: type=gha
cache-to: type=gha,mode=max

# Multi-stage builds
FROM python:3.11-slim as builder
COPY requirements.txt .
RUN pip install --user -r requirements.txt

FROM python:3.11-slim
COPY --from=builder /root/.local /root/.local
```

### **Deployment Optimization**
```bash
# Parallel service deployment
docker-compose up -d --parallel

# Health check optimization
--health-interval=5s
--health-timeout=3s
--health-retries=3
```

---

## 🚨 **Troubleshooting**

### **Common Issues**

#### **Build Failures**
```bash
# Check build logs
docker-compose logs [service-name]

# Verify dependencies
pip list
npm list
```

#### **Deployment Failures**
```bash
# Check service status
docker-compose ps

# Check health status
docker-compose ps --format "table {{.Name}}\t{{.Status}}\t{{.Health}}"

# View recent logs
docker-compose logs --tail=100 [service-name]
```

#### **Performance Issues**
```bash
# Check resource usage
docker stats

# Monitor network
docker exec [container] netstat -i

# Check disk usage
docker system df
```

---

## 📚 **Useful Commands**

### **Deployment Commands**
```bash
# Deploy to staging
./scripts/deploy-ci-cd.sh -e staging -t rolling

# Deploy to production
./scripts/deploy-ci-cd.sh -e production -t blue-green

# Check deployment status
docker-compose -f docker-compose.cloud.yml ps

# View logs
docker-compose -f docker-compose.cloud.yml logs -f
```

### **Maintenance Commands**
```bash
# Update images
docker-compose -f docker-compose.cloud.yml pull

# Restart services
docker-compose -f docker-compose.cloud.yml restart

# Clean up
docker-compose -f docker-compose.cloud.yml down --volumes --remove-orphans
```

---

## 🎉 **Next Steps**

1. **Choose your CI/CD platform** (GitHub Actions recommended)
2. **Set up repository secrets** for AWS credentials
3. **Create environments** (staging, production)
4. **Test the pipeline** with a small change
5. **Monitor deployments** and adjust as needed
6. **Add notifications** (Slack, email, etc.)
7. **Implement advanced strategies** (blue-green, canary)

This CI/CD setup will give you **automated testing**, **secure deployments**, and **zero-downtime updates** for your Study AI Platform! 🚀
