# SageMaker Ollama Deployment Troubleshooting Guide

## Common Issues and Solutions

### 1. Manifest Error at CreateModel

**Problem**: Your ECR image is still OCI format instead of Docker v2 Schema 2.

**Solution**: 
1. Re-run the GitHub Action to build and push the image
2. Verify manifest type:
```bash
aws ecr batch-get-image --repository-name ollama-inference \
  --image-ids imageTag=sm-compat-v2 \
  --query 'images[0].imageManifestMediaType' --output text \
  --region ap-southeast-1
# Must return: application/vnd.docker.distribution.manifest.v2+json
```

**Root Cause**: Docker Desktop on macOS produces OCI manifests by default. The GitHub Action builds on Linux and uses skopeo to force Docker v2 schema.

### 2. Endpoint Failed to Start

**Problem**: SageMaker endpoint fails to come up or stays in "Failed" status.

**Diagnosis**: Check CloudWatch logs:
```bash
aws logs tail "/aws/sagemaker/Endpoints/studium-dev-ollama-minimal-endpoint" \
  --region ap-southeast-1 --since 1h
```

**Common Fixes**:

#### Model Too Large
- **Symptom**: Container fails to start or crashes
- **Solution**: Use quantized model (e.g., `llama3:8b-instruct-q4_K_M`) or larger instance type

#### Port Binding Issues
- **Symptom**: Gunicorn not binding to port 8080
- **Solution**: Ensure Dockerfile exposes 8080 and start.sh binds to 0.0.0.0:8080

#### Missing /ping Endpoint
- **Symptom**: SageMaker health checks fail
- **Solution**: Verify inference.py has `/ping` route returning 200 OK

#### Network Connectivity
- **Symptom**: Container can't pull models from internet
- **Solution**: Deploy without VPC first, or ensure NAT Gateway in private subnets

### 3. IAM Permission Issues

**Problem**: Container can't pull from ECR or write to CloudWatch.

**Solution**: Verify execution role has:
- `ecr:GetAuthorizationToken`
- `ecr:BatchCheckLayerAvailability` 
- `ecr:GetDownloadUrlForLayer`
- `ecr:BatchGetImage`
- `logs:CreateLogGroup`, `logs:CreateLogStream`, `logs:PutLogEvents`
- `s3:GetObject`, `s3:PutObject`, `s3:ListBucket`

**Check**: Look for "Access Denied" errors in CloudWatch logs.

### 4. Container Startup Issues

**Problem**: Container starts but Ollama or Gunicorn fails.

**Diagnosis**: Check container logs for:
- Ollama service not starting
- Model download failures
- Gunicorn binding errors

**Common Issues**:

#### Ollama Service
- **Symptom**: "ollama serve" command fails
- **Solution**: Verify Ollama binary is copied correctly in Dockerfile

#### Model Download
- **Symptom**: Model pull timeout or failure
- **Solution**: Check internet connectivity, use smaller model, or pre-load model

#### Gunicorn Binding
- **Symptom**: "Address already in use" or binding errors
- **Solution**: Ensure only one service binds to port 8080

### 5. Performance Issues

**Problem**: Endpoint responds slowly or times out.

**Diagnosis**: Check CloudWatch metrics:
- ModelLatency
- Invocation4XXErrors
- Invocation5XXErrors

**Solutions**:
- Use larger instance type (e.g., `ml.g5.xlarge` for GPU)
- Optimize model (quantization)
- Increase Gunicorn timeout in start.sh

### 6. Validation Script Failures

**Problem**: `validate-endpoint.sh` fails.

**Common Issues**:

#### Endpoint Not InService
- Wait for endpoint to finish deployment (5-15 minutes)
- Check CloudWatch logs for startup errors

#### Permission Denied
- Ensure AWS credentials are configured
- Verify IAM permissions for SageMaker operations

#### Network Issues
- Check VPC configuration if using private subnets
- Verify security groups allow SageMaker traffic

## Debugging Commands

### Check Endpoint Status
```bash
aws sagemaker describe-endpoint \
  --endpoint-name studium-dev-ollama-minimal-endpoint \
  --region ap-southeast-1
```

### View CloudWatch Logs
```bash
aws logs tail "/aws/sagemaker/Endpoints/studium-dev-ollama-minimal-endpoint" \
  --region ap-southeast-1 --since 30m
```

### Test Endpoint
```bash
aws sagemaker-runtime invoke-endpoint \
  --endpoint-name studium-dev-ollama-minimal-endpoint \
  --content-type application/json \
  --body '{"prompt":"test"}' \
  /dev/stdout
```

### Check ECR Image
```bash
aws ecr describe-images \
  --repository-name ollama-inference \
  --region ap-southeast-1
```

## Prevention Best Practices

1. **Always build on Linux**: Use GitHub Actions or AWS CodeBuild
2. **Test locally first**: Use Docker to test container startup
3. **Monitor logs**: Set up CloudWatch alarms for errors
4. **Start simple**: Deploy without VPC first, add complexity later
5. **Use appropriate instance types**: Start with CPU instances for testing

## Getting Help

1. Check CloudWatch logs first
2. Verify ECR image manifest type
3. Test with simple prompts
4. Check IAM permissions
5. Review network configuration

If issues persist, collect:
- CloudWatch logs
- ECR image details
- IAM role policies
- Network configuration
- Error messages from SageMaker console

