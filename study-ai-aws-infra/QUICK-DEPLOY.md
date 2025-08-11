# 🚀 Quick Deployment Reference

## 📋 Current Status
- ✅ EC2 running at: `54.251.86.190`
- ✅ S3 bucket: `studyai-uploads-dev-ap-southeast-1`
- ✅ Docker & Nginx ready
- ✅ SSH key: `infra/studyai_key`

## 🚀 Fast Deploy (3 Steps)

### 1. SSH into EC2
```bash
make ssh
```

### 2. Deploy App (Choose One)

**Option A: Docker Run**
```bash
docker run -d \
  --name studyai-app \
  --restart unless-stopped \
  -p 3000:3000 \
  -e NODE_ENV=production \
  -e AWS_REGION=ap-southeast-1 \
  -e S3_BUCKET=studyai-uploads-dev-ap-southeast-1 \
  your-registry/studyai-app:latest
```

**Option B: Docker Compose**
```bash
# Upload docker-compose.yml first, then:
docker-compose up -d
```

### 3. Verify Deployment
```bash
# Check if running
docker ps

# Test app
curl http://localhost:3000

# Check logs
docker logs studyai-app
```

## 🌐 Access Your App
- **External**: `http://54.251.86.190`
- **Direct**: `http://54.251.86.190:3000`

## 🔧 Common Commands
```bash
# View logs
docker logs studyai-app -f

# Restart app
docker restart studyai-app

# Stop app
docker stop studyai-app

# Remove app
docker rm studyai-app
```

## 🆘 Need Help?
- **Full Guide**: See `DEPLOYMENT.md`
- **Troubleshooting**: Check container logs
- **Infrastructure**: Use `make` commands
