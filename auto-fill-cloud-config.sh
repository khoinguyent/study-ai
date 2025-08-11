#!/bin/bash

# Auto-fill Cloud Configuration Script for Study AI Platform
# This script extracts infrastructure details from Terraform and fills env.cloud

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
TERRAFORM_DIR="study-ai-aws-infra/infra"
CONFIG_FILE="env.cloud"
EXAMPLE_FILE="env.cloud.example"

echo -e "${BLUE}🔧 Auto-fill Cloud Configuration Script${NC}"
echo -e "${BLUE}=======================================${NC}"
echo ""

# Check if Terraform directory exists
if [ ! -d "$TERRAFORM_DIR" ]; then
    echo -e "${RED}❌ Terraform directory not found: $TERRAFORM_DIR${NC}"
    echo -e "${YELLOW}Please ensure you're running this script from the study-ai root directory.${NC}"
    exit 1
fi

# Check if env.cloud.example exists
if [ ! -f "$EXAMPLE_FILE" ]; then
    echo -e "${RED}❌ Example configuration file not found: $EXAMPLE_FILE${NC}"
    echo -e "${YELLOW}Please ensure env.cloud.example exists.${NC}"
    exit 1
fi

# Change to Terraform directory
cd "$TERRAFORM_DIR"

# Check if Terraform is initialized
if [ ! -f ".terraform/terraform.tfstate" ]; then
    echo -e "${YELLOW}⚠️  Terraform not initialized or no state file found.${NC}"
    echo -e "${YELLOW}Please run 'terraform init' and 'terraform apply' first.${NC}"
    echo ""
    echo -e "${BLUE}📋 To set up the missing infrastructure, run:${NC}"
    echo -e "  cd $TERRAFORM_DIR"
    echo -e "  terraform init"
    echo -e "  terraform apply"
    echo ""
    exit 1
fi

# Check if Terraform outputs are available
if ! terraform output > /dev/null 2>&1; then
    echo -e "${RED}❌ No Terraform outputs found.${NC}"
    echo -e "${YELLOW}Please run 'terraform apply' to create the infrastructure first.${NC}"
    exit 1
fi

echo -e "${BLUE}📊 Extracting Terraform outputs...${NC}"

# Extract Terraform outputs
BUCKET_NAME=$(terraform output -raw bucket_name 2>/dev/null || echo "")
EC2_PUBLIC_IP=$(terraform output -raw ec2_public_ip 2>/dev/null || echo "")
AWS_REGION=$(terraform output -raw region 2>/dev/null || echo "us-east-1")

# Extract new infrastructure outputs
REDIS_ENDPOINT=$(terraform output -raw redis_endpoint 2>/dev/null || echo "")
REDIS_PORT=$(terraform output -raw redis_port 2>/dev/null || echo "")
REDIS_URL=$(terraform output -raw redis_url 2>/dev/null || echo "")
MESSAGE_BROKER_URL=$(terraform output -raw message_broker_url 2>/dev/null || echo "")
TASK_QUEUE_URL=$(terraform output -raw task_queue_url 2>/dev/null || echo "")

# Get AWS account ID
AWS_ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text 2>/dev/null || echo "")

echo -e "${GREEN}✅ Terraform outputs extracted successfully${NC}"
echo ""

# Go back to root directory
cd - > /dev/null

# Create env.cloud from example
echo -e "${BLUE}📝 Creating env.cloud configuration...${NC}"
cp "$EXAMPLE_FILE" "$CONFIG_FILE"

echo -e "${GREEN}✅ Created $CONFIG_FILE from template${NC}"
echo ""

# Auto-fill what we can from Terraform
echo -e "${BLUE}🔧 Auto-filling configuration with Terraform outputs...${NC}"

# Update S3 bucket name if available
if [ -n "$BUCKET_NAME" ]; then
    sed -i.bak "s/S3_BUCKET=.*/S3_BUCKET=$BUCKET_NAME/" "$CONFIG_FILE"
    echo -e "${GREEN}✅ S3_BUCKET set to: $BUCKET_NAME${NC}"
else
    echo -e "${YELLOW}⚠️  S3_BUCKET not found in Terraform outputs${NC}"
fi

# Update AWS region if available
if [ -n "$AWS_REGION" ]; then
    sed -i.bak "s/AWS_REGION=.*/AWS_REGION=$AWS_REGION/" "$CONFIG_FILE"
    sed -i.bak "s/SQS_REGION=.*/SQS_REGION=$AWS_REGION/" "$CONFIG_FILE"
    sed -i.bak "s/S3_REGION=.*/S3_REGION=$AWS_REGION/" "$CONFIG_FILE"
    sed -i.bak "s/CLOUDWATCH_REGION=.*/CLOUDWATCH_REGION=$AWS_REGION/" "$CONFIG_FILE"
    echo -e "${GREEN}✅ AWS_REGION set to: $AWS_REGION${NC}"
else
    echo -e "${YELLOW}⚠️  AWS_REGION not found in Terraform outputs${NC}"
fi

# Update AWS account ID if available
if [ -n "$AWS_ACCOUNT_ID" ]; then
    # Update SQS queue URL placeholder with account ID
    sed -i.bak "s/your-account-id/$AWS_ACCOUNT_ID/g" "$CONFIG_FILE"
    echo -e "${GREEN}✅ AWS_ACCOUNT_ID set to: $AWS_ACCOUNT_ID${NC}"
else
    echo -e "${YELLOW}⚠️  AWS_ACCOUNT_ID not available${NC}"
fi

# Update Redis/ElastiCache configuration if available
if [ -n "$REDIS_ENDPOINT" ]; then
    sed -i.bak "s/REDIS_HOST=.*/REDIS_HOST=$REDIS_ENDPOINT/" "$CONFIG_FILE"
    echo -e "${GREEN}✅ REDIS_HOST set to: $REDIS_ENDPOINT${NC}"
else
    echo -e "${YELLOW}⚠️  REDIS_HOST not found in Terraform outputs${NC}"
fi

if [ -n "$REDIS_PORT" ]; then
    sed -i.bak "s/REDIS_PORT=.*/REDIS_PORT=$REDIS_PORT/" "$CONFIG_FILE"
    echo -e "${GREEN}✅ REDIS_PORT set to: $REDIS_PORT${NC}"
else
    echo -e "${YELLOW}⚠️  REDIS_PORT not found in Terraform outputs${NC}"
fi

# Update message broker URL if available
if [ -n "$MESSAGE_BROKER_URL" ]; then
    sed -i.bak "s|MESSAGE_BROKER_URL=.*|MESSAGE_BROKER_URL=$MESSAGE_BROKER_URL|" "$CONFIG_FILE"
    echo -e "${GREEN}✅ MESSAGE_BROKER_URL set to: $MESSAGE_BROKER_URL${NC}"
else
    echo -e "${YELLOW}⚠️  MESSAGE_BROKER_URL not found in Terraform outputs${NC}"
fi

# Update task queue URL if available
if [ -n "$TASK_QUEUE_URL" ]; then
    sed -i.bak "s|TASK_QUEUE_URL=.*|TASK_QUEUE_URL=$TASK_QUEUE_URL|" "$CONFIG_FILE"
    sed -i.bak "s|SQS_QUEUE_URL=.*|SQS_QUEUE_URL=$TASK_QUEUE_URL|" "$CONFIG_FILE"
    echo -e "${GREEN}✅ TASK_QUEUE_URL set to: $TASK_QUEUE_URL${NC}"
else
    echo -e "${YELLOW}⚠️  TASK_QUEUE_URL not found in Terraform outputs${NC}"
fi

# Remove backup files
rm -f "$CONFIG_FILE.bak"

echo ""
echo -e "${BLUE}📋 Configuration Status:${NC}"

# Check what's configured and what's missing
echo -e "${BLUE}✅ Auto-filled from Terraform:${NC}"
if [ -n "$BUCKET_NAME" ]; then echo -e "  📦 S3_BUCKET: $BUCKET_NAME"; fi
if [ -n "$AWS_REGION" ]; then echo -e "  🌍 AWS_REGION: $AWS_REGION"; fi
if [ -n "$AWS_ACCOUNT_ID" ]; then echo -e "  🔑 AWS_ACCOUNT_ID: $AWS_ACCOUNT_ID"; fi
if [ -n "$REDIS_ENDPOINT" ]; then echo -e "  📡 REDIS_HOST: $REDIS_ENDPOINT"; fi
if [ -n "$MESSAGE_BROKER_URL" ]; then echo -e "  📡 MESSAGE_BROKER_URL: $MESSAGE_BROKER_URL"; fi
if [ -n "$TASK_QUEUE_URL" ]; then echo -e "  📋 TASK_QUEUE_URL: $TASK_QUEUE_URL"; fi

echo ""
echo -e "${YELLOW}⚠️  Still need to configure manually:${NC}"
echo -e "  🔐 AWS_ACCESS_KEY_ID"
echo -e "  🔐 AWS_SECRET_ACCESS_KEY"
echo -e "  🔐 DATABASE_PASSWORD (for containerized databases)"

echo ""
echo -e "${BLUE}🔧 Next Steps:${NC}"

echo -e "${YELLOW}1. Set database password in env.cloud:${NC}"
echo -e "   - Edit $CONFIG_FILE"
echo -e "   - Change DATABASE_PASSWORD=your-secure-password"
echo -e "   - This password will be used by all database containers"
echo ""

echo -e "${YELLOW}2. Get AWS credentials:${NC}"
echo -e "   - Create IAM user with appropriate permissions"
echo -e "   - Generate access key and secret key"
echo ""

echo -e "${YELLOW}3. Update $CONFIG_FILE with:${NC}"
echo -e "   - AWS_ACCESS_KEY_ID"
echo -e "   - AWS_SECRET_ACCESS_KEY"
echo ""

echo -e "${YELLOW}4. Deploy:${NC}"
echo -e "   ./deploy-cloud.sh"
echo -e "   # This will create all database containers with your password"
echo ""

echo -e "${BLUE}💡 Pro Tips:${NC}"
echo -e "  - Use 'terraform output' to see all available outputs"
echo -e "  - Check AWS Console for service endpoints"
echo -e "  - Ensure security groups allow access from your IP"
echo -e "  - Run 'terraform apply' again if you added new resources"
echo -e "  - Database containers will be created automatically with your password"
echo -e "  - No need to manually set up PostgreSQL on EC2 anymore"

echo ""
echo -e "${GREEN}🎉 Auto-fill completed!${NC}"
echo -e "${BLUE}📁 Configuration file: $CONFIG_FILE${NC}"

# Show what's still needed
echo ""
echo -e "${BLUE}🔍 To see all Terraform outputs:${NC}"
echo -e "  cd $TERRAFORM_DIR && terraform output"

echo ""
echo -e "${BLUE}🔐 Database Password Setup:${NC}"
echo -e "  1. Set DATABASE_PASSWORD in $CONFIG_FILE"
echo -e "  2. All database containers will use this password automatically"
echo -e "  3. No manual PostgreSQL setup required - everything runs in containers"
