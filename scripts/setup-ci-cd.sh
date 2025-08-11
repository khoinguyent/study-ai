#!/bin/bash

# CI/CD Setup Script for Study AI Platform
# This script helps set up the CI/CD pipeline

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}🚀 Study AI Platform CI/CD Setup${NC}"
echo -e "${BLUE}================================${NC}"
echo ""

# Check if we're in a git repository
if [[ ! -d ".git" ]]; then
    echo -e "${RED}❌ Not in a git repository${NC}"
    echo -e "${YELLOW}Please run this script from your project root directory${NC}"
    exit 1
fi

# Check if GitHub Actions workflow exists
if [[ ! -f ".github/workflows/ci-cd.yml" ]]; then
    echo -e "${RED}❌ GitHub Actions workflow not found${NC}"
    echo -e "${YELLOW}Please ensure .github/workflows/ci-cd.yml exists${NC}"
    exit 1
fi

echo -e "${GREEN}✅ Git repository and GitHub Actions workflow found${NC}"
echo ""

# Get repository information
REPO_URL=$(git remote get-url origin)
REPO_NAME=$(basename -s .git "$REPO_URL")

echo -e "${BLUE}📋 Repository Information:${NC}"
echo -e "  Name: ${GREEN}$REPO_NAME${NC}"
echo -e "  URL: ${GREEN}$REPO_URL${NC}"
echo ""

# Check if GitHub CLI is installed
if command -v gh &> /dev/null; then
    echo -e "${GREEN}✅ GitHub CLI found${NC}"
    
    # Check if user is authenticated
    if gh auth status &> /dev/null; then
        echo -e "${GREEN}✅ GitHub CLI authenticated${NC}"
        
        # Get current user
        CURRENT_USER=$(gh api user --jq .login)
        echo -e "  User: ${GREEN}$CURRENT_USER${NC}"
    else
        echo -e "${YELLOW}⚠️  GitHub CLI not authenticated${NC}"
        echo -e "${BLUE}Please run: gh auth login${NC}"
    fi
else
    echo -e "${YELLOW}⚠️  GitHub CLI not found${NC}"
    echo -e "${BLUE}Install from: https://cli.github.com/${NC}"
fi

echo ""

# Display setup instructions
echo -e "${BLUE}🔧 CI/CD Setup Instructions:${NC}"
echo ""

echo -e "${YELLOW}1. Enable GitHub Actions:${NC}"
echo -e "   - Go to: https://github.com/$CURRENT_USER/$REPO_NAME/actions"
echo -e "   - Click 'New workflow'"
echo -e "   - Choose 'Skip this and set up a workflow yourself'"
echo -e "   - Copy the contents of .github/workflows/ci-cd.yml"
echo ""

echo -e "${YELLOW}2. Set up Repository Secrets:${NC}"
echo -e "   - Go to: https://github.com/$CURRENT_USER/$REPO_NAME/settings/secrets/actions"
echo -e "   - Add the following secrets:"
echo ""

echo -e "${BLUE}   AWS Staging Environment:${NC}"
echo -e "     AWS_ACCESS_KEY_ID_STAGING"
echo -e "     AWS_SECRET_ACCESS_KEY_STAGING"
echo -e "     AWS_REGION_STAGING"
echo ""

echo -e "${BLUE}   AWS Production Environment:${NC}"
echo -e "     AWS_ACCESS_KEY_ID_PROD"
echo -e "     AWS_SECRET_ACCESS_KEY_PROD"
echo -e "     AWS_REGION_PROD"
echo ""

echo -e "${BLUE}   Security Scanning:${NC}"
echo -e "     SNYK_TOKEN (optional)"
echo ""

echo -e "${YELLOW}3. Create Environments:${NC}"
echo -e "   - Go to: https://github.com/$CURRENT_USER/$REPO_NAME/settings/environments"
echo -e "   - Create 'staging' environment"
echo -e "   - Create 'production' environment (with protection rules)"
echo ""

echo -e "${YELLOW}4. Test the Pipeline:${NC}"
echo -e "   - Make a small change to your code"
echo -e "   - Push to a feature branch"
echo -e "   - Create a pull request"
echo -e "   - Check the Actions tab for pipeline execution"
echo ""

# Check if required files exist
echo -e "${BLUE}📁 Required Files Check:${NC}"

REQUIRED_FILES=(
    ".github/workflows/ci-cd.yml"
    "scripts/deploy-ci-cd.sh"
    "docker-compose.cloud.yml"
    "env.cloud.example"
)

for file in "${REQUIRED_FILES[@]}"; do
    if [[ -f "$file" ]]; then
        echo -e "  ✅ $file"
    else
        echo -e "  ❌ $file (missing)"
    fi
done

echo ""

# Check if environment files exist
echo -e "${BLUE}🔐 Environment Configuration:${NC}"
if [[ -f "env.cloud" ]]; then
    echo -e "  ✅ env.cloud (exists)"
else
    echo -e "  ❌ env.cloud (missing - run ./auto-fill-cloud-config.sh first)"
fi

if [[ -f "env.local.example" ]]; then
    echo -e "  ✅ env.local.example (exists)"
else
    echo -e "  ❌ env.local.example (missing)"
fi

echo ""

# Display next steps
echo -e "${BLUE}🎯 Next Steps:${NC}"
echo ""

if [[ -f "env.cloud" ]]; then
    echo -e "${GREEN}✅ Your environment is ready for CI/CD!${NC}"
    echo -e "  - Follow the setup instructions above"
    echo -e "  - Test with a small change"
    echo -e "  - Monitor pipeline execution"
else
    echo -e "${YELLOW}⚠️  Environment not configured yet${NC}"
    echo -e "  - Run: ./auto-fill-cloud-config.sh"
    echo -e "  - Configure: env.cloud"
    echo -e "  - Then follow CI/CD setup instructions"
fi

echo ""

# Display useful commands
echo -e "${BLUE}📚 Useful Commands:${NC}"
echo -e "  # Test deployment locally"
echo -e "  ./scripts/deploy-ci-cd.sh -e staging -t rolling"
echo -e ""
echo -e "  # Check service status"
echo -e "  docker-compose -f docker-compose.cloud.yml ps"
echo -e ""
echo -e "  # View logs"
echo -e "  docker-compose -f docker-compose.cloud.yml logs -f"
echo -e ""
echo -e "  # Clean up"
echo -e "  docker-compose -f docker-compose.cloud.yml down --volumes --remove-orphans"

echo ""
echo -e "${GREEN}🎉 CI/CD setup guide completed!${NC}"
echo -e "${BLUE}📖 For detailed information, see: CI_CD_GUIDE.md${NC}"
