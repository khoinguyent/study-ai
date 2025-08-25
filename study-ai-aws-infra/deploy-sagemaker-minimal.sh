#!/bin/bash

# Deploy Minimal SageMaker for Ollama Model (Quiz Generation Only)
# This script deploys only the essential SageMaker resources needed for quiz generation
# No development environment, notebooks, or user profiles

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Script configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
INFRA_DIR="$SCRIPT_DIR/infra"
PROJECT_NAME="Studium-app"
PROJECT_SHORT="studium"

echo -e "${BLUE}🚀 ${PROJECT_NAME} - Minimal SageMaker Deployment${NC}"
echo -e "${BLUE}================================================${NC}"
echo ""

# Check if we're in the right directory
if [[ ! -f "$INFRA_DIR/main.tf" ]]; then
    echo -e "${RED}❌ Error: Please run this script from the study-ai-aws-infra directory${NC}"
    exit 1
fi

# Check if Terraform is installed
if ! command -v terraform &> /dev/null; then
    echo -e "${RED}❌ Error: Terraform is not installed${NC}"
    echo "Please install Terraform first: https://www.terraform.io/downloads.html"
    exit 1
fi

# Check if AWS CLI is installed and configured
if ! command -v aws &> /dev/null; then
    echo -e "${RED}❌ Error: AWS CLI is not installed${NC}"
    echo "Please install AWS CLI first: https://aws.amazon.com/cli/"
    exit 1
fi

# Check AWS credentials
if ! aws sts get-caller-identity &> /dev/null; then
    echo -e "${RED}❌ Error: AWS credentials not configured${NC}"
    echo "Please run 'aws configure' first"
    exit 1
fi

echo -e "${GREEN}✅ Prerequisites check passed${NC}"
echo ""

# Get current AWS account and region
AWS_ACCOUNT=$(aws sts get-caller-identity --query Account --output text)
AWS_REGION=$(aws configure get region)
echo -e "${BLUE}📋 AWS Configuration:${NC}"
echo "   Account: $AWS_ACCOUNT"
echo "   Region:  $AWS_REGION"
echo ""

# Check if ECR repository exists and has the Ollama image
echo -e "${BLUE}🔍 Checking ECR repository for Ollama image...${NC}"
ECR_REPO_NAME="ollama-inference"
ECR_REPO_URI="$AWS_ACCOUNT.dkr.ecr.$AWS_REGION.amazonaws.com/$ECR_REPO_NAME"

if ! aws ecr describe-repositories --repository-names "$ECR_REPO_NAME" &> /dev/null; then
    echo -e "${YELLOW}⚠️  ECR repository '$ECR_REPO_NAME' not found${NC}"
    echo "   You need to build and push the Ollama image first"
    echo "   Run: ./build-and-push.sh"
    echo ""
    read -p "Do you want to continue anyway? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo -e "${RED}❌ Deployment cancelled${NC}"
        exit 1
    fi
else
    echo -e "${GREEN}✅ ECR repository found: $ECR_REPO_URI${NC}"
    
    # Check if image exists
    if aws ecr describe-images --repository-name "$ECR_REPO_NAME" --query 'imageDetails[0].imageTags' --output text &> /dev/null; then
        echo -e "${GREEN}✅ Ollama image found in ECR${NC}"
    else
        echo -e "${YELLOW}⚠️  No images found in ECR repository${NC}"
        echo "   You need to build and push the Ollama image first"
        echo "   Run: ./build-and-push.sh"
        echo ""
        read -p "Do you want to continue anyway? (y/N): " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            echo -e "${RED}❌ Deployment cancelled${NC}"
            exit 1
        fi
    fi
fi

# Navigate to infrastructure directory
cd "$INFRA_DIR"

# Initialize Terraform if needed
if [[ ! -d ".terraform" ]]; then
    echo -e "${BLUE}🔧 Initializing Terraform...${NC}"
    terraform init
    echo -e "${GREEN}✅ Terraform initialized${NC}"
else
    echo -e "${GREEN}✅ Terraform already initialized${NC}"
fi

# Create terraform.tfvars for minimal SageMaker
echo -e "${BLUE}📝 Creating terraform.tfvars for minimal SageMaker...${NC}"
cat > terraform.tfvars << EOF
# Minimal SageMaker Configuration for Quiz Generation
enable_sagemaker = false
enable_sagemaker_minimal = true

# Ollama Model Configuration
ollama_model_name = "llama2:7b-chat"
ollama_image_uri = "$ECR_REPO_URI:latest"

# Instance Configuration (cost-optimized)
sagemaker_minimal_instance_type = "ml.t3.small"
sagemaker_minimal_initial_count = 1
sagemaker_minimal_max_count = 3
sagemaker_minimal_min_count = 0

# Security and Monitoring
enable_kms_encryption = true
enable_cloudwatch_monitoring = true
enable_vpc_endpoints = true

# Environment
env = "dev"
project = "Studium-app"
project_short = "studium"
region = "$AWS_REGION"

# Cost Center
cost_center = "AI-Research"
project_owner = "Study AI Team"
EOF

echo -e "${GREEN}✅ terraform.tfvars created${NC}"
echo ""

# Show configuration
echo -e "${BLUE}📋 Deployment Configuration:${NC}"
echo "   SageMaker Type: Minimal (Model + Endpoint only)"
echo "   Purpose: Quiz Generation"
echo "   Ollama Model: llama2:7b-chat"
echo "   Instance Type: ml.t3.small (cost-optimized)"
echo "   Auto-scaling: 0-3 instances"
echo "   Encryption: KMS enabled"
echo "   Monitoring: CloudWatch enabled"
echo ""

# Confirm deployment
echo -e "${YELLOW}⚠️  This will deploy minimal SageMaker resources for quiz generation only${NC}"
echo "   Estimated cost: ~$0.10-0.30/hour when active"
echo "   Resources will scale to zero when not in use"
echo ""
read -p "Proceed with deployment? (y/N): " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo -e "${RED}❌ Deployment cancelled${NC}"
    exit 1
fi

# Plan deployment
echo -e "${BLUE}📋 Planning Terraform deployment...${NC}"
if ! terraform plan -var-file="terraform.tfvars" -out=tfplan; then
    echo -e "${RED}❌ Terraform plan failed${NC}"
    exit 1
fi

echo -e "${GREEN}✅ Terraform plan completed${NC}"
echo ""

# Show plan summary
echo -e "${BLUE}📊 Plan Summary:${NC}"
terraform show tfplan | grep -E "(Plan:|  \+ |  ~ |  - )" | head -20
echo ""

# Confirm apply
read -p "Apply this plan? (y/N): " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo -e "${YELLOW}⚠️  Plan applied but deployment cancelled${NC}"
    echo "   Run 'terraform apply tfplan' manually if needed"
    exit 1
fi

# Apply deployment
echo -e "${BLUE}🚀 Applying Terraform deployment...${NC}"
if terraform apply tfplan; then
    echo -e "${GREEN}✅ Deployment completed successfully!${NC}"
else
    echo -e "${RED}❌ Deployment failed${NC}"
    exit 1
fi

# Get deployment outputs
echo ""
echo -e "${BLUE}📊 Deployment Outputs:${NC}"
terraform output -json | jq -r 'to_entries[] | "\(.key): \(.value)"' 2>/dev/null || {
    echo "   Endpoint Name: $(terraform output -raw sagemaker_minimal_endpoint_name 2>/dev/null || echo 'N/A')"
    echo "   Endpoint ARN: $(terraform output -raw sagemaker_minimal_endpoint_arn 2>/dev/null || echo 'N/A')"
    echo "   Model ARN: $(terraform output -raw sagemaker_minimal_model_arn 2>/dev/null || echo 'N/A')"
    echo "   S3 Bucket: $(terraform output -raw sagemaker_minimal_s3_bucket_name 2>/dev/null || echo 'N/A')"
}

# Clean up plan file
rm -f tfplan

echo ""
echo -e "${GREEN}🎉 Minimal SageMaker deployment completed!${NC}"
echo ""
echo -e "${BLUE}📚 Next Steps:${NC}"
echo "   1. Test the endpoint with a quiz generation request"
echo "   2. Monitor performance in CloudWatch dashboard"
echo "   3. Configure auto-scaling policies if needed"
echo "   4. Set up cost alerts for budget monitoring"
echo ""
echo -e "${BLUE}🔗 Useful Links:${NC}"
echo "   AWS Console: https://$AWS_REGION.console.aws.amazon.com/sagemaker/"
echo "   CloudWatch: https://$AWS_REGION.console.aws.amazon.com/cloudwatch/"
echo "   Resource Groups: https://$AWS_REGION.console.aws.amazon.com/resource-groups/"
echo ""
echo -e "${BLUE}💰 Cost Optimization Tips:${NC}"
echo "   • Instance scales to zero when not in use"
echo "   • Use CloudWatch alarms to monitor costs"
echo "   • Consider reserved instances for production"
echo "   • Monitor auto-scaling metrics"
echo ""
echo -e "${GREEN}✅ Your Ollama model is now ready for quiz generation!${NC}"
