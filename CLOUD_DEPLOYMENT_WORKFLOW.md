# Cloud Deployment Workflow - Study AI Platform

## 🎯 **Overview**

This document explains the complete workflow for deploying the Study AI Platform to AWS cloud using the new auto-fill infrastructure configuration system.

## 🏗️ **Architecture Summary**

- **Message Broker**: Redis → **ElastiCache**
- **Task Queue**: Celery → **SQS** 
- **Database**: Local PostgreSQL → **Containerized PostgreSQL** (same as local)
- **Storage**: MinIO → **S3**
- **LLM**: Ollama → **SageMaker** (optional)

## 🚀 **Complete Deployment Workflow**

### **Phase 1: Infrastructure Setup**

#### **1.1 Deploy AWS Infrastructure**
```bash
cd study-ai-aws-infra/infra
terraform init
terraform apply
```

This creates:
- ✅ ElastiCache Redis cluster
- ✅ SQS queues (main, document, indexing, quiz, DLQ)
- ✅ S3 bucket for document storage
- ✅ EC2 instance (for other purposes, not PostgreSQL)
- ✅ Security groups and IAM roles

#### **1.2 Verify Infrastructure**
```bash
terraform output
```

You should see outputs for:
- `redis_endpoint`
- `main_tasks_queue_url`
- `bucket_name`
- `ec2_public_ip`

### **Phase 2: Auto-Configuration**

#### **2.1 Run Auto-Fill Script**
```bash
# From study-ai root directory
./auto-fill-cloud-config.sh
```

**What gets auto-filled:**
- ✅ S3_BUCKET
- ✅ AWS_REGION  
- ✅ AWS_ACCOUNT_ID
- ✅ REDIS_HOST
- ✅ MESSAGE_BROKER_URL
- ✅ TASK_QUEUE_URL

**What you still need to set:**
- 🔐 AWS_ACCESS_KEY_ID
- 🔐 AWS_SECRET_ACCESS_KEY
- 🔐 DATABASE_PASSWORD

#### **2.2 Configure Remaining Variables**
Edit `env.cloud`:
```bash
# Set your AWS credentials
AWS_ACCESS_KEY_ID=AKIA...
AWS_SECRET_ACCESS_KEY=your-secret-key

# Set a secure database password
DATABASE_PASSWORD=your-secure-password
```

### **Phase 3: Deploy Services**

#### **3.1 Deploy to Cloud**
```bash
./deploy-cloud.sh
```

This will:
- ✅ Build all service images
- ✅ Create all database containers with your password
- ✅ Start services with cloud configuration
- ✅ Use ElastiCache instead of Redis
- ✅ Use SQS instead of Celery
- ✅ Use containerized PostgreSQL (same as local)

#### **3.2 Verify Deployment**
```bash
docker-compose -f docker-compose.cloud.yml ps
docker-compose -f docker-compose.cloud.yml logs -f
```

## 🔧 **Configuration Files**

### **env.cloud**
- Main configuration file for cloud environment
- Created automatically by auto-fill script
- Contains all infrastructure endpoints and credentials
- **DATABASE_PASSWORD** is used by all database containers

### **docker-compose.cloud.yml**
- Cloud-specific deployment configuration
- Uses env.cloud for all environment variables
- **Includes all database services** (same as local setup)
- No local Redis/Celery dependencies

## 📊 **What Gets Auto-Filled vs Manual**

| Configuration | Auto-Filled | Manual Setup |
|---------------|-------------|--------------|
| **S3_BUCKET** | ✅ Terraform | ❌ |
| **AWS_REGION** | ✅ Terraform | ❌ |
| **REDIS_HOST** | ✅ ElastiCache | ❌ |
| **MESSAGE_BROKER_URL** | ✅ ElastiCache | ❌ |
| **TASK_QUEUE_URL** | ✅ SQS | ❌ |
| **Database services** | ✅ Docker Compose | ❌ |
| **AWS credentials** | ❌ | ✅ IAM user |
| **Database password** | ❌ | ✅ env.cloud |

## 🚨 **Common Issues & Solutions**

### **Issue 1: "Missing required environment variables"**
**Solution**: Run `./auto-fill-cloud-config.sh` first, then manually set AWS credentials.

### **Issue 2: "Cannot connect to ElastiCache"**
**Solutions**:
- Check security group allows access from your IP
- Verify ElastiCache endpoint is correct
- Check IAM permissions

### **Issue 3: "Cannot connect to SQS"**
**Solutions**:
- Verify SQS queue URL is correct
- Check IAM user has SQS permissions
- Verify AWS region matches

### **Issue 4: "Database connection failed"**
**Solutions**:
- Ensure DATABASE_PASSWORD is set in env.cloud
- Check database containers are running
- Verify database health checks are passing

## 💡 **Pro Tips**

1. **Start Small**: Use t3.micro instances for testing
2. **Security Groups**: Ensure they allow access from your IP
3. **IAM Permissions**: Grant minimum required permissions
4. **Password Consistency**: Set DATABASE_PASSWORD once in env.cloud
5. **Region Consistency**: Keep all resources in the same AWS region
6. **Database Containers**: All databases run in containers (no EC2 setup needed)

## 🔄 **Updating Infrastructure**

### **Add New Resources**
```bash
cd study-ai-aws-infra/infra
# Edit Terraform files
terraform plan
terraform apply
```

### **Update Configuration**
```bash
# Re-run auto-fill to get new endpoints
./auto-fill-cloud-config.sh
```

### **Redeploy Services**
```bash
./deploy-cloud.sh
```

## 📚 **Useful Commands**

### **View Infrastructure Status**
```bash
cd study-ai-aws-infra/infra
terraform output
terraform show
```

### **View Service Logs**
```bash
docker-compose -f docker-compose.cloud.yml logs -f
docker-compose -f docker-compose.cloud.yml logs [service-name]
```

### **View Database Logs**
```bash
docker-compose -f docker-compose.cloud.yml logs -f auth-db
docker-compose -f docker-compose.cloud.yml logs -f document-db
docker-compose -f docker-compose.cloud.yml logs -f indexing-db
```

### **Restart Services**
```bash
docker-compose -f docker-compose.cloud.yml restart
docker-compose -f docker-compose.cloud.yml restart [service-name]
```

### **Clean Up**
```bash
docker-compose -f docker-compose.cloud.yml down --volumes --remove-orphans
```

## 🎉 **Success Indicators**

Your cloud deployment is successful when:
- ✅ All services show "running" status
- ✅ All database containers show "healthy" status
- ✅ No connection errors in logs
- ✅ Services can connect to ElastiCache
- ✅ Services can connect to SQS
- ✅ Services can connect to database containers
- ✅ Document uploads work
- ✅ Task processing works via SQS

## 🆘 **Need Help?**

1. **Check Logs**: `docker-compose -f docker-compose.cloud.yml logs -f`
2. **Verify AWS**: Check AWS Console for service status
3. **Test Connectivity**: Use verification commands from setup scripts
4. **Review Configuration**: Double-check all environment variables
5. **Check Database Health**: Ensure all database containers are healthy

---

## 📁 **File Structure**

```
study-ai/
├── auto-fill-cloud-config.sh          # Auto-fills env.cloud from Terraform
├── deploy-cloud.sh                    # Deploys services to cloud
├── env.cloud                          # Cloud configuration (auto-created)
├── env.cloud.example                  # Template for cloud configuration
├── docker-compose.cloud.yml           # Cloud deployment configuration
│   ├── Database services              # auth-db, document-db, indexing-db, etc.
│   ├── Application services           # api-gateway, auth-service, etc.
│   └── Uses env.cloud for config     # All passwords and endpoints
├── study-ai-aws-infra/                # Terraform infrastructure
│   └── infra/
│       ├── main.tf                    # EC2, S3, security groups
│       ├── elasticache.tf             # ElastiCache Redis
│       ├── sqs.tf                     # SQS queues
│       ├── variables.tf               # Terraform variables
│       └── outputs.tf                 # Infrastructure outputs
└── services/                          # Application services
```

## 🔐 **Database Setup**

**No manual PostgreSQL setup required!** 

- **DATABASE_PASSWORD** in env.cloud is used by all database containers
- **All 5 databases** are created automatically:
  - `auth_db` (port 5432)
  - `document_db` (port 5433)
  - `indexing_db` (port 5434) - with pgvector
  - `quiz_db` (port 5435)
  - `notification_db` (port 5437)
- **Health checks** ensure databases are ready before services start
- **Same setup as local** - just with cloud infrastructure for Redis/Celery

This workflow makes cloud deployment much simpler by automatically configuring most of the infrastructure endpoints and keeping the same database setup as local! 🚀
