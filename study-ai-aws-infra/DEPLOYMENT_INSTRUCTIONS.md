# SageMaker Ollama Deployment Instructions

## Prerequisites

1. **AWS CLI configured** with appropriate permissions
2. **Terraform** installed (version >= 1.0)
3. **Docker** running locally (for testing)
4. **GitHub repository** with access to AWS (for CI/CD)

## Step-by-Step Deployment

### 1. Build and Push Docker Image

#### Option A: GitHub Actions (Recommended)
1. **Set up GitHub repository secrets**:
   - `AWS_OIDC_ROLE_ARN`: IAM role with ECR push permissions
   
2. **Push code to trigger workflow**:
   ```bash
   git add .
   git commit -m "Add SageMaker Ollama deployment"
   git push origin main
   ```

3. **Monitor GitHub Actions**:
   - Workflow will build Linux image
   - Use skopeo to ensure Docker v2 Schema 2
   - Push to ECR with `sm-compat-v2` tag

#### Option B: Local Build (macOS - may have OCI manifest issues)
```bash
cd ollama-sagemaker
export ECR_URI=YOUR_ACCOUNT_ID.dkr.ecr.ap-southeast-1.amazonaws.com/ollama-inference
export ECR_REPO=ollama-inference

# Install skopeo for schema conversion
brew install skopeo

# Build and push
./build-and-push.sh
```

### 2. Verify ECR Image

Ensure the image is Docker v2 Schema 2 (not OCI):
```bash
aws ecr batch-get-image \
  --repository-name ollama-inference \
  --image-ids imageTag=sm-compat-v2 \
  --query 'images[0].imageManifestMediaType' --output text \
  --region ap-southeast-1

# Must return: application/vnd.docker.distribution.manifest.v2+json
```

### 3. Deploy Infrastructure

```bash
cd infra

# Initialize Terraform
terraform init -upgrade

# Plan deployment
terraform plan

# Apply configuration
terraform apply -auto-approve
```

**Expected Resources Created**:
- SageMaker Model
- SageMaker Endpoint Configuration  
- SageMaker Endpoint
- IAM Role with execution permissions
- S3 Bucket for models/data
- CloudWatch Log Group
- CloudWatch Dashboard
- CloudWatch Alarms

### 4. Monitor Deployment

**Check endpoint status**:
```bash
aws sagemaker describe-endpoint \
  --endpoint-name studium-dev-ollama-minimal-endpoint \
  --region ap-southeast-1 \
  --query 'EndpointStatus'
```

**Expected progression**:
1. `Creating` → `InService` (5-15 minutes)
2. If `Failed`, check CloudWatch logs

**View logs**:
```bash
aws logs tail "/aws/sagemaker/Endpoints/studium-dev-ollama-minimal-endpoint" \
  --region ap-southeast-1 --since 30m
```

### 5. Validate Endpoint

Run the validation script:
```bash
cd ..
AWS_REGION=ap-southeast-1 ./scripts/validate-endpoint.sh
```

**Expected output**:
- ✅ Endpoint is InService
- ✅ Inference test passed
- Quiz generation response

## Configuration Options

### Instance Types

**CPU-only** (slower, cheaper):
- `ml.m7i.xlarge` - 4 vCPU, 16 GB RAM
- `ml.c6i.xlarge` - 4 vCPU, 8 GB RAM

**GPU** (faster, more expensive):
- `ml.g5.xlarge` - 4 vCPU, 24 GB RAM + GPU
- `ml.p3.2xlarge` - 8 vCPU, 61 GB RAM + GPU

**Update in `terraform.tfvars`**:
```hcl
sagemaker_minimal_instance_type = "ml.g5.xlarge"
```

### Model Configuration

**Default model**: `llama3:8b-instruct`

**Quantized alternatives** (faster, smaller):
- `llama3:8b-instruct-q4_K_M`
- `llama3:8b-instruct-q5_K_M`

**Update in `terraform.tfvars`**:
```hcl
ollama_model_name = "llama3:8b-instruct-q4_K_M"
```

### Environment Variables

**Container environment** (set in Terraform):
- `OLLAMA_MODEL`: Model to use
- `OLLAMA_PRELOAD`: Whether to pre-load model
- `PORT`: HTTP port (must be 8080)

## Testing

### 1. Basic Health Check
```bash
aws sagemaker describe-endpoint \
  --endpoint-name studium-dev-ollama-minimal-endpoint \
  --region ap-southeast-1
```

### 2. Simple Inference
```bash
aws sagemaker-runtime invoke-endpoint \
  --endpoint-name studium-dev-ollama-minimal-endpoint \
  --content-type application/json \
  --body '{"prompt":"Hello, how are you?"}' \
  /dev/stdout
```

### 3. Quiz Generation
```bash
aws sagemaker-runtime invoke-endpoint \
  --endpoint-name studium-dev-ollama-minimal-endpoint \
  --content-type application/json \
  --body '{"prompt":"Generate 3 multiple choice questions about Vietnam history."}' \
  /dev/stdout
```

## Troubleshooting

### Common Issues

1. **Manifest Type Error**: Image is OCI format
   - Re-run GitHub Action or use skopeo locally
   
2. **Endpoint Failed**: Check CloudWatch logs
   - Model too large → use quantized version
   - Port binding → verify Dockerfile exposes 8080
   
3. **Permission Denied**: Check IAM role
   - Ensure ECR pull permissions
   - Verify CloudWatch log permissions

### Debug Commands

```bash
# Check endpoint status
aws sagemaker describe-endpoint --endpoint-name studium-dev-ollama-minimal-endpoint

# View logs
aws logs tail "/aws/sagemaker/Endpoints/studium-dev-ollama-minimal-endpoint" --since 1h

# Test endpoint
aws sagemaker-runtime invoke-endpoint --endpoint-name studium-dev-ollama-minimal-endpoint --content-type application/json --body '{"prompt":"test"}' /dev/stdout
```

## Cost Optimization

### Instance Selection
- **Development**: Use CPU instances (`ml.m7i.xlarge`)
- **Production**: Use GPU instances (`ml.g5.xlarge`)

### Auto-scaling
- Start with 1 instance
- Add auto-scaling based on demand
- Use Spot instances for cost savings

### Model Optimization
- Use quantized models for faster inference
- Consider smaller models for simple tasks

## Security Considerations

1. **Network**: Deploy in private subnets with NAT Gateway
2. **Encryption**: Use KMS for S3 and SageMaker encryption
3. **IAM**: Follow principle of least privilege
4. **Monitoring**: Set up CloudWatch alarms for errors

## Next Steps

1. **Production Deployment**:
   - Add auto-scaling
   - Implement monitoring and alerting
   - Set up CI/CD pipeline
   
2. **Model Management**:
   - Version control for models
   - A/B testing capabilities
   - Model performance monitoring
   
3. **Integration**:
   - Connect to your application
   - Implement caching layer
   - Add rate limiting

## Support

- **Documentation**: Check `TROUBLESHOOTING.md`
- **Logs**: CloudWatch logs for debugging
- **Metrics**: CloudWatch dashboard for monitoring
- **Issues**: GitHub repository issues

