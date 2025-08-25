# AWS SageMaker Integration for Ollama Models

This guide explains how to deploy and use Ollama models in AWS SageMaker for the Study AI application.

## Overview

The SageMaker integration provides a scalable, managed environment for running Ollama models in production. Instead of running Ollama locally in Docker containers, you can now:

- Deploy models to managed SageMaker endpoints
- Scale automatically based on demand
- Use AWS IAM for security and access control
- Monitor performance and costs through AWS CloudWatch
- Integrate with other AWS services seamlessly

## Architecture

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Study AI App  │───▶│  SageMaker       │───▶│   Ollama        │
│                 │    │  Endpoint        │    │   Model         │
└─────────────────┘    └──────────────────┘    └─────────────────┘
                              │
                              ▼
                       ┌──────────────────┐
                       │  S3 Bucket       │
                       │  (Models/Data)   │
                       └──────────────────┘
```

## Prerequisites

- AWS CLI configured with appropriate credentials
- Terraform >= 1.6.0
- Docker (for building the container image)
- jq (optional, for JSON parsing)

## Quick Start

### 1. Build and Push Container Image

First, build the Ollama SageMaker container and push it to Amazon ECR:

```bash
cd ollama-sagemaker
chmod +x build-and-push.sh
./build-and-push.sh --region ap-southeast-1 --tag latest
```

This script will:
- Create an ECR repository if it doesn't exist
- Build the Docker image with Ollama and SageMaker inference code
- Push the image to ECR
- Display the image URI for use in Terraform

### 2. Deploy SageMaker Infrastructure

Deploy the SageMaker infrastructure using the provided script:

```bash
chmod +x deploy-sagemaker.sh
./deploy-sagemaker.sh
```

Or manually with Terraform:

```bash
cd infra
terraform init
terraform plan -var="enable_sagemaker=true"
terraform apply -var="enable_sagemaker=true"
```

### 3. Update Application Configuration

Update your application to use the SageMaker endpoint instead of local Ollama:

```bash
# Get the endpoint URL
terraform output sagemaker_endpoint_url

# Update environment variables
export SAGEMAKER_ENDPOINT_URL="<endpoint-url>"
export OLLAMA_BASE_URL="<endpoint-url>"
```

## Configuration

### Terraform Variables

The following variables control the SageMaker deployment:

| Variable | Description | Default |
|-----------|-------------|---------|
| `enable_sagemaker` | Enable SageMaker infrastructure | `false` |
| `sagemaker_instance_type` | Instance type for notebooks | `ml.t3.medium` |
| `sagemaker_image_arn` | SageMaker image ARN | PyTorch 1.13.1 CPU |
| `ollama_image_uri` | ECR image URI for Ollama | Auto-detected |
| `sagemaker_endpoint_instance_type` | Endpoint instance type | `ml.t3.medium` |
| `sagemaker_endpoint_initial_count` | Initial instance count | `1` |

### Environment Variables

Set these environment variables in your application:

```bash
# SageMaker Configuration
SAGEMAKER_ENDPOINT_URL="https://<endpoint-name>.execute-api.<region>.amazonaws.com"
SAGEMAKER_REGION="ap-southeast-1"
SAGEMAKER_ROLE_ARN="arn:aws:iam::<account>:role/<role-name>"

# Ollama Model Configuration
OLLAMA_MODEL="llama2:7b-chat"
OLLAMA_TEMPERATURE="0.7"
OLLAMA_MAX_TOKENS="1000"
```

## Usage

### Invoking the Endpoint

#### Using AWS CLI

```bash
# Test the endpoint
aws sagemaker-runtime invoke-endpoint \
    --endpoint-name "studyai-dev-ollama-endpoint" \
    --content-type application/json \
    --input '{"prompt": "Hello, how are you?", "temperature": 0.7}' \
    --output response.json \
    --region ap-southeast-1

# View response
cat response.json
```

#### Using Python

```python
import boto3
import json

# Initialize SageMaker runtime client
runtime = boto3.client('sagemaker-runtime', region_name='ap-southeast-1')

# Prepare input
input_data = {
    "prompt": "Hello, how are you?",
    "temperature": 0.7,
    "max_tokens": 100
}

# Invoke endpoint
response = runtime.invoke_endpoint(
    EndpointName='studyai-dev-ollama-endpoint',
    ContentType='application/json',
    Body=json.dumps(input_data)
)

# Parse response
result = json.loads(response['Body'].read().decode())
print(result['response'])
```

#### Using cURL

```bash
curl -X POST \
    -H "Content-Type: application/json" \
    -H "Authorization: Bearer $(aws sts get-session-token --query Credentials.SessionToken --output text)" \
    -d '{"prompt": "Hello, how are you?", "temperature": 0.7}' \
    "https://<endpoint-name>.execute-api.<region>.amazonaws.com/invocations"
```

### Model Management

#### Pulling New Models

The SageMaker container automatically pulls models when they're requested. To pre-load models:

```bash
# Access SageMaker Studio
# Navigate to the domain URL from terraform output

# Or use the AWS CLI to pull models
aws sagemaker create-model-package \
    --model-package-name "ollama-llama2" \
    --model-package-description "Llama2 model for Ollama" \
    --region ap-southeast-1
```

#### Updating Models

To update models, you'll need to:

1. Build a new container image with the updated model
2. Push to ECR with a new tag
3. Update the SageMaker model
4. Update the endpoint configuration

```bash
# Build new image
./build-and-push.sh --tag v1.1.0

# Update Terraform configuration
terraform apply -var="ollama_image_uri=<new-image-uri>"
```

## Monitoring and Logging

### CloudWatch Metrics

SageMaker automatically provides metrics for:
- Invocation count
- Invocation errors
- Model latency
- CPU/GPU utilization
- Memory usage

### CloudWatch Logs

Access logs through the SageMaker console or AWS CLI:

```bash
# Get log streams
aws logs describe-log-groups --log-group-name-prefix "/aws/sagemaker"

# Get log events
aws logs get-log-events \
    --log-group-name "/aws/sagemaker/studyai-dev-ollama-endpoint" \
    --log-stream-name "<stream-name>"
```

## Cost Optimization

### Instance Types

Choose appropriate instance types based on your workload:

- **ml.t3.medium**: Good for development and testing
- **ml.c5.xlarge**: Better performance for production
- **ml.g4dn.xlarge**: GPU acceleration for faster inference

### Auto Scaling

Configure auto-scaling to optimize costs:

```hcl
# In your Terraform configuration
resource "aws_sagemaker_endpoint_configuration" "ollama_endpoint" {
  # ... existing configuration ...
  
  production_variants {
    variant_name           = "default"
    model_name            = aws_sagemaker_model.ollama_model[0].name
    instance_type         = var.sagemaker_endpoint_instance_type
    initial_instance_count = var.sagemaker_endpoint_initial_count
    
    # Auto scaling configuration
    auto_scaling_policy {
      target_tracking_scaling_policy_configuration {
        target_value = 70.0
        predefined_metric_specification {
          predefined_metric_type = "SageMakerVariantInvocationsPerInstance"
        }
      }
    }
  }
}
```

## Security

### IAM Roles and Policies

The deployment creates IAM roles with least-privilege access:

- **SageMaker Execution Role**: Can access S3, ECR, and CloudWatch
- **EC2 Role**: Can access S3 for uploads

### VPC Configuration

SageMaker runs in your VPC with:
- Private subnets for model endpoints
- Security groups controlling access
- NAT gateways for internet access

### Encryption

All data is encrypted:
- S3 buckets use AES256 encryption
- SageMaker endpoints use KMS encryption
- Network traffic uses TLS 1.2+

## Troubleshooting

### Common Issues

#### Endpoint Not Responding

```bash
# Check endpoint status
aws sagemaker describe-endpoint --endpoint-name "studyai-dev-ollama-endpoint"

# Check CloudWatch logs
aws logs tail "/aws/sagemaker/studyai-dev-ollama-endpoint" --follow
```

#### Model Loading Issues

```bash
# Check container logs
aws logs describe-log-streams \
    --log-group-name "/aws/sagemaker/studyai-dev-ollama-endpoint" \
    --order-by LastEventTime \
    --descending
```

#### Permission Issues

```bash
# Verify IAM role permissions
aws iam get-role --role-name "studyai-dev-sagemaker-role"
aws iam list-attached-role-policies --role-name "studyai-dev-sagemaker-role"
```

### Debug Mode

Enable debug logging in the container:

```dockerfile
# In Dockerfile
ENV SAGEMAKER_CONTAINER_LOG_LEVEL=10
```

## Migration from Local Ollama

### 1. Update Environment Variables

```bash
# Before (Local)
OLLAMA_BASE_URL=http://localhost:11434

# After (SageMaker)
OLLAMA_BASE_URL=https://<endpoint-url>
```

### 2. Update Application Code

```python
# Before: Direct Ollama API calls
import requests

response = requests.post(
    "http://localhost:11434/api/generate",
    json={"model": "llama2:7b-chat", "prompt": "Hello"}
)

# After: SageMaker endpoint calls
import boto3

runtime = boto3.client('sagemaker-runtime')
response = runtime.invoke_endpoint(
    EndpointName='studyai-dev-ollama-endpoint',
    ContentType='application/json',
    Body=json.dumps({"prompt": "Hello"})
)
```

### 3. Test Migration

```bash
# Test local endpoint
curl -X POST http://localhost:11434/api/generate \
    -d '{"model": "llama2:7b-chat", "prompt": "Hello"}'

# Test SageMaker endpoint
aws sagemaker-runtime invoke-endpoint \
    --endpoint-name "studyai-dev-ollama-endpoint" \
    --content-type application/json \
    --input '{"prompt": "Hello"}' \
    --output response.json
```

## Support

For issues and questions:

1. Check CloudWatch logs for detailed error messages
2. Review SageMaker console for endpoint status
3. Verify IAM permissions and VPC configuration
4. Check Terraform outputs for resource information

## Next Steps

After successful deployment:

1. **Monitor Performance**: Use CloudWatch metrics to optimize instance types
2. **Scale Up**: Configure auto-scaling for production workloads
3. **Add Models**: Deploy additional Ollama models to different endpoints
4. **Integrate**: Update your application to use SageMaker endpoints
5. **Optimize**: Fine-tune models and configurations for your use case
