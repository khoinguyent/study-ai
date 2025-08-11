# 🚀 Study AI Application Deployment Guide

This guide explains how to deploy your Study AI application to the EC2 instance and integrate it with AWS services.

## 📋 Prerequisites

- ✅ EC2 instance running (deployed via Terraform)
- ✅ SSH access to EC2 instance
- ✅ Docker installed on EC2
- ✅ S3 bucket created
- ✅ IAM roles configured

## 🔧 Current Infrastructure Status

Your EC2 instance is already configured with:
- **Nginx** reverse proxy (port 80 → 3000)
- **Docker** runtime
- **S3 bucket**: `studyai-uploads-dev-ap-southeast-1`
- **IAM role** with S3 permissions

## 🚀 Deployment Options

### Option 1: Docker Container Deployment (Recommended)

#### Step 1: SSH into EC2
```bash
make ssh
# or manually: ssh -i infra/studyai_key ubuntu@54.251.86.190
```

#### Step 2: Deploy using the script
```bash
# Upload the deployment script
# (You'll need to copy this from your local machine)

# Make it executable
chmod +x deploy-app.sh

# Run the deployment
./deploy-app.sh
```

#### Step 3: Deploy using Docker Compose
```bash
# Upload docker-compose.yml to EC2
# Then run:
docker-compose up -d

# Check status
docker-compose ps
docker-compose logs -f studyai-app
```

### Option 2: Manual Docker Deployment

```bash
# SSH into EC2
make ssh

# Pull and run your application
docker run -d \
  --name studyai-app \
  --restart unless-stopped \
  -p 3000:3000 \
  -e NODE_ENV=production \
  -e AWS_REGION=ap-southeast-1 \
  -e S3_BUCKET=studyai-uploads-dev-ap-southeast-1 \
  your-registry/studyai-app:latest

# Check if running
docker ps
curl http://localhost:3000
```

### Option 3: Direct Application Deployment

```bash
# SSH into EC2
make ssh

# Install Node.js (if Node.js app)
curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
sudo apt-get install -y nodejs

# Clone your application
git clone https://github.com/your-org/study-ai.git
cd study-ai

# Install dependencies
npm install

# Set environment variables
export NODE_ENV=production
export AWS_REGION=ap-southeast-1
export S3_BUCKET=studyai-uploads-dev-ap-southeast-1

# Start the application
npm start
```

## 🔄 AWS Service Integration

### 1. Replace MinIO with S3

Your S3 bucket is already configured. Update your application to use AWS SDK:

```javascript
// Example: Replace MinIO client with AWS SDK
import { S3Client, PutObjectCommand, GetObjectCommand } from '@aws-sdk/client-s3';

const s3Client = new S3Client({
  region: process.env.AWS_REGION || 'ap-southeast-1'
});

// Upload file
const uploadFile = async (key, body) => {
  const command = new PutObjectCommand({
    Bucket: process.env.S3_BUCKET,
    Key: key,
    Body: body
  });
  return await s3Client.send(command);
};
```

### 2. Replace Queue Services with AWS SQS

Add SQS permissions to your EC2 IAM role and update your app:

```javascript
import { SQSClient, SendMessageCommand } from '@aws-sdk/client-sqs';

const sqsClient = new SQSClient({
  region: process.env.AWS_REGION || 'ap-southeast-1'
});

// Send message to queue
const sendMessage = async (queueUrl, messageBody) => {
  const command = new SendMessageCommand({
    QueueUrl: queueUrl,
    MessageBody: JSON.stringify(messageBody)
  });
  return await sqsClient.send(command);
};
```

### 3. Additional AWS Services to Consider

| Current Service | AWS Replacement | Benefits |
|----------------|-----------------|----------|
| Local Database | AWS RDS | Managed, scalable, backup |
| Local Redis | AWS ElastiCache | Managed, scalable, high availability |
| Local Storage | AWS S3 | Scalable, durable, cost-effective |
| Local Queue | AWS SQS | Reliable, scalable, managed |
| Local Monitoring | AWS CloudWatch | Comprehensive monitoring |

## 🌐 Application Access

### External Access
Your application will be accessible at:
- **HTTP**: `http://54.251.86.190` (Nginx proxy)
- **Direct**: `http://54.251.86.190:3000` (if needed)

### Health Check
Add a health check endpoint to your application:
```javascript
app.get('/health', (req, res) => {
  res.status(200).json({ status: 'healthy', timestamp: new Date().toISOString() });
});
```

## 📊 Monitoring & Logs

### Container Logs
```bash
# View application logs
docker logs studyai-app -f

# View Nginx logs
sudo tail -f /var/log/nginx/access.log
sudo tail -f /var/log/nginx/error.log
```

### System Monitoring
```bash
# Check system resources
htop
df -h
free -h

# Check Docker resources
docker stats
```

## 🔒 Security Considerations

### Current Configuration
- ✅ SSH key-based authentication
- ✅ Security groups configured
- ✅ IAM roles with least privilege
- ⚠️ SSH open to all IPs (0.0.0.0/0)

### Security Improvements
```bash
# Restrict SSH to your IP only
make apply-secure

# Or manually update terraform.tfvars
allow_ssh_cidr = "YOUR_IP_ADDRESS/32"
```

## 🚨 Troubleshooting

### Common Issues

#### 1. Application not responding
```bash
# Check if container is running
docker ps

# Check container logs
docker logs studyai-app

# Check if port is listening
netstat -tlnp | grep 3000
```

#### 2. Nginx proxy issues
```bash
# Check Nginx status
sudo systemctl status nginx

# Test Nginx configuration
sudo nginx -t

# Check Nginx logs
sudo tail -f /var/log/nginx/error.log
```

#### 3. S3 access issues
```bash
# Test S3 access from EC2
aws s3 ls s3://studyai-uploads-dev-ap-southeast-1

# Check IAM role
aws sts get-caller-identity
```

### Debug Commands
```bash
# Check all running containers
docker ps -a

# Check container resource usage
docker stats

# Check system resources
top
free -h
df -h

# Check network connectivity
curl -v http://localhost:3000
curl -v http://127.0.0.1:3000
```

## 📝 Environment Variables

Your application should use these environment variables:

```bash
# Required
NODE_ENV=production
AWS_REGION=ap-southeast-1
S3_BUCKET=studyai-uploads-dev-ap-southeast-1
PORT=3000

# Optional (add as needed)
# DATABASE_URL=your-database-url
# REDIS_URL=your-redis-url
# JWT_SECRET=your-jwt-secret
# LOG_LEVEL=info
```

## 🔄 Deployment Workflow

### Development → Production
1. **Build** your application
2. **Push** Docker image to registry
3. **SSH** into EC2
4. **Pull** latest image
5. **Restart** container
6. **Verify** deployment

### Automated Deployment
Consider setting up:
- **GitHub Actions** for CI/CD
- **AWS CodeDeploy** for automated deployments
- **Docker Hub** or **ECR** for image management

## 🧹 Cleanup

### Stop Application
```bash
# Stop container
docker stop studyai-app

# Remove container
docker rm studyai-app

# Or use Docker Compose
docker-compose down
```

### Destroy Infrastructure
```bash
# When completely done
make destroy
```

## 📚 Next Steps

1. **Deploy your application** using one of the methods above
2. **Test the integration** with S3 and other AWS services
3. **Monitor performance** and logs
4. **Plan migration** to additional AWS services (RDS, ElastiCache, etc.)
5. **Set up CI/CD** for automated deployments

## 🆘 Getting Help

- Check container logs: `docker logs studyai-app`
- Check Nginx logs: `sudo tail -f /var/log/nginx/error.log`
- Verify AWS permissions: `aws sts get-caller-identity`
- Test connectivity: `curl -v http://localhost:3000`

---

**Note**: This guide assumes your application is containerized. If you need help with the application code or have specific requirements, please share the source code or requirements.
