#!/bin/bash

# Setup PostgreSQL on EC2 Instance
# This script helps set up PostgreSQL with the password from env.cloud

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

echo -e "${BLUE}🗄️  EC2 PostgreSQL Setup Script${NC}"
echo -e "${BLUE}==============================${NC}"
echo ""

# Check if env.cloud exists
if [ ! -f "$CONFIG_FILE" ]; then
    echo -e "${RED}❌ Configuration file $CONFIG_FILE not found!${NC}"
    echo -e "${YELLOW}Please run ./auto-fill-cloud-config.sh first to create it.${NC}"
    exit 1
fi

# Check if Terraform directory exists
if [ ! -d "$TERRAFORM_DIR" ]; then
    echo -e "${RED}❌ Terraform directory not found: $TERRAFORM_DIR${NC}"
    echo -e "${YELLOW}Please ensure you're running this script from the study-ai root directory.${NC}"
    exit 1
fi

# Extract database password from env.cloud
DATABASE_PASSWORD=$(grep "^DATABASE_PASSWORD=" "$CONFIG_FILE" | cut -d'=' -f2 | tr -d '"' | tr -d "'")

if [ -z "$DATABASE_PASSWORD" ] || [ "$DATABASE_PASSWORD" = "your-secure-password" ]; then
    echo -e "${RED}❌ DATABASE_PASSWORD not set in $CONFIG_FILE${NC}"
    echo -e "${YELLOW}Please edit $CONFIG_FILE and set DATABASE_PASSWORD to a secure password.${NC}"
    exit 1
fi

echo -e "${GREEN}✅ Database password found: ${DATABASE_PASSWORD:0:8}...${NC}"

# Get EC2 public IP from Terraform
cd "$TERRAFORM_DIR"

if [ ! -f ".terraform/terraform.tfstate" ]; then
    echo -e "${RED}❌ Terraform not initialized or no state file found.${NC}"
    echo -e "${YELLOW}Please run 'terraform init' and 'terraform apply' first.${NC}"
    exit 1
fi

EC2_PUBLIC_IP=$(terraform output -raw ec2_public_ip 2>/dev/null || echo "")

if [ -z "$EC2_PUBLIC_IP" ]; then
    echo -e "${RED}❌ EC2 public IP not found in Terraform outputs.${NC}"
    echo -e "${YELLOW}Please ensure EC2 instance is created and running.${NC}"
    exit 1
fi

echo -e "${GREEN}✅ EC2 public IP: $EC2_PUBLIC_IP${NC}"

# Go back to root directory
cd - > /dev/null

echo ""
echo -e "${BLUE}📋 PostgreSQL Setup Instructions for EC2:${NC}"
echo ""

echo -e "${YELLOW}1. SSH to your EC2 instance:${NC}"
echo -e "   ssh -i $TERRAFORM_DIR/studyai_key ubuntu@$EC2_PUBLIC_IP"
echo ""

echo -e "${YELLOW}2. Install PostgreSQL:${NC}"
echo -e "   sudo apt update"
echo -e "   sudo apt install -y postgresql postgresql-contrib"
echo ""

echo -e "${YELLOW}3. Start PostgreSQL service:${NC}"
echo -e "   sudo systemctl start postgresql"
echo -e "   sudo systemctl enable postgresql"
echo ""

echo -e "${YELLOW}4. Switch to postgres user:${NC}"
echo -e "   sudo -i -u postgres"
echo ""

echo -e "${YELLOW}5. Create the study_ai database:${NC}"
echo -e "   createdb study_ai"
echo ""

echo -e "${YELLOW}6. Set the password (use the password from env.cloud):${NC}"
echo -e "   psql -c \"ALTER USER postgres PASSWORD '$DATABASE_PASSWORD';\""
echo ""

echo -e "${YELLOW}7. Exit postgres user:${NC}"
echo -e "   exit"
echo ""

echo -e "${YELLOW}8. Configure PostgreSQL to accept connections:${NC}"
echo -e "   sudo nano /etc/postgresql/*/main/postgresql.conf"
echo -e "   # Change: listen_addresses = '*'"
echo ""

echo -e "${YELLOW}9. Configure client authentication:${NC}"
echo -e "   sudo nano /etc/postgresql/*/main/pg_hba.conf"
echo -e "   # Add: host all all 0.0.0.0/0 md5"
echo ""

echo -e "${YELLOW}10. Restart PostgreSQL:${NC}"
echo -e "    sudo systemctl restart postgresql"
echo ""

echo -e "${YELLOW}11. Test connection:${NC}"
echo -e "    psql -h $EC2_PUBLIC_IP -U postgres -d study_ai"
echo -e "    # Enter password: $DATABASE_PASSWORD"
echo ""

echo -e "${BLUE}🔐 Important Notes:${NC}"
echo -e "  - Use the EXACT password: $DATABASE_PASSWORD"
echo -e "  - This password is already configured in $CONFIG_FILE"
echo -e "  - All services will use this password automatically"
echo -e "  - Ensure port 5432 is open in your EC2 security group"
echo ""

echo -e "${GREEN}🎉 After completing these steps, your database will be ready!${NC}"
echo -e "${BLUE}📁 You can then run: ./deploy-cloud.sh${NC}"
