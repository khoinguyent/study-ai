# Cloud Setup Guide for Study AI Platform

## 🚀 **Quick Start (5 Steps)**

### **Step 1: Copy Configuration Template**
```bash
cp env.cloud.example env.cloud
```

### **Step 2: Get AWS Infrastructure Endpoints**
You need to create these AWS resources first:
- **ElastiCache** (Redis cluster)
- **SQS** (message queue)
- **RDS** (PostgreSQL database)
- **S3** (object storage)

### **Step 3: Configure Environment Variables**
Edit `env.cloud` with your actual values:

```bash
# Required: Environment
ENVIRONMENT=cloud
INFRASTRUCTURE_PROVIDER=aws

# Required: Message Broker (ElastiCache)
MESSAGE_BROKER_TYPE=elasticache
MESSAGE_BROKER_URL=redis://your-elasticache-endpoint:6379

# Required: Task Queue (SQS)
TASK_QUEUE_TYPE=sqs
TASK_QUEUE_URL=https://sqs.us-east-1.amazonaws.com/your-account-id/your-queue-name

# Required: AWS Credentials
AWS_REGION=us-east-1
AWS_ACCESS_KEY_ID=AKIA...
AWS_SECRET_ACCESS_KEY=your-secret-key
```

### **Step 4: Deploy**
```bash
./deploy-cloud.sh
```

### **Step 5: Verify**
Check that all services are running:
```bash
docker-compose -f docker-compose.cloud.yml ps
```

## 🔧 **What You Must Configure Manually**

### **MESSAGE_BROKER_URL is NOT auto-filled!**

You must manually set these values in `env.cloud`:

1. **ElastiCache Endpoint**: Get from AWS Console → ElastiCache
2. **SQS Queue URL**: Get from AWS Console → SQS
3. **AWS Credentials**: Create IAM user with appropriate permissions
4. **Database Endpoint**: Get from AWS Console → RDS

## 🚨 **Common Issues**

- **"Missing MESSAGE_BROKER_URL"**: You must set this manually
- **"AWS credentials invalid"**: Check IAM user permissions
- **"Cannot connect to ElastiCache"**: Verify security groups and endpoint
- **"SQS access denied"**: Check IAM policies

## 💡 **Pro Tips**

1. **Start Small**: Use t3.micro instances for testing
2. **Security Groups**: Ensure they allow your IP/EC2 access
3. **IAM Permissions**: Grant minimum required permissions
4. **Region Consistency**: Keep all resources in the same AWS region
