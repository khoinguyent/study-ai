# Studium-app AWS Infrastructure

## Important Notes

### Region Consistency
- **SageMaker model image and endpoint must be in the same region as the ECR repository.**
- Default region is `ap-southeast-1` where the ECR repo exists.
- Ensure `AWS_PROFILE` and `AWS_DEFAULT_REGION` (or `var.region`) match before running apply.

### SageMaker Deployment Requirements
- Docker images must use Docker v2 Schema 2 manifest (not OCI manifest)
- Avoid `buildx --push` which defaults to OCI format
- Use `buildx --load` + `docker push` to ensure Docker v2 compatibility

## Quick Start

### 1. Build and Push Docker Image
```bash
cd ollama-sagemaker
export ECR_URI=542834090270.dkr.ecr.ap-southeast-1.amazonaws.com/ollama-inference
export ECR_REPO=ollama-inference

# Build and push with Docker v2 compatibility
docker buildx create --use --name smbuilder || true
docker buildx build --platform linux/amd64 --load -t ${ECR_URI}:sm-compat-v2 .
aws ecr get-login-password --region ap-southeast-1 | docker login --username AWS --password-stdin 542834090270.dkr.ecr.ap-southeast-1.amazonaws.com
docker push ${ECR_URI}:sm-compat-v2

# Verify manifest type
aws ecr batch-get-image --repository-name ${ECR_REPO} \
  --image-ids imageTag=sm-compat-v2 \
  --query 'images[0].imageManifestMediaType' --output text
# Should return: application/vnd.docker.distribution.manifest.v2+json
```

### 2. Deploy Infrastructure
```bash
cd infra
terraform init -upgrade
terraform apply -auto-approve
```

### 3. Test SageMaker Endpoint
```bash
aws sagemaker invoke-endpoint \
  --endpoint-name <your-endpoint-name> \
  --body '{"prompt":"ping"}' \
  --content-type application/json \
  /dev/stdout
```

## Architecture

This infrastructure deploys:
- **Minimal SageMaker**: Model + Endpoint for Ollama inference
- **Security**: IAM roles, KMS encryption, VPC endpoints
- **Monitoring**: CloudWatch logs, dashboards, alarms
- **Resource Groups**: Tag-based organization for easy management

## Troubleshooting

### Common Issues
1. **OCI Manifest Error**: Ensure you're using `--load` + `docker push`, not `buildx --push`
2. **Region Mismatch**: Verify ECR repo and SageMaker are in the same region
3. **Resource Groups**: Using `AWS::AllSupported` with tag filters for compatibility
