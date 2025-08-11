#!/bin/bash

# Setup Branching Strategy Script for Study AI Platform
# This script creates the proper branch structure for multi-environment CI/CD

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}🌿 Setting up Branching Strategy${NC}"
echo -e "${BLUE}===============================${NC}"
echo ""

# Check if we're in a git repository
if [[ ! -d ".git" ]]; then
    echo -e "${RED}❌ Not in a git repository${NC}"
    echo -e "${YELLOW}Please run this script from your project root directory${NC}"
    exit 1
fi

# Check if we have remote origin
if ! git remote get-url origin &> /dev/null; then
    echo -e "${RED}❌ No remote origin found${NC}"
    echo -e "${YELLOW}Please add a remote origin first:${NC}"
    echo -e "  git remote add origin <your-repo-url>"
    exit 1
fi

# Get current branch
CURRENT_BRANCH=$(git branch --show-current)
echo -e "${BLUE}📋 Current branch: ${GREEN}$CURRENT_BRANCH${NC}"

# Check if we're on main branch
if [[ "$CURRENT_BRANCH" != "main" ]]; then
    echo -e "${YELLOW}⚠️  You're not on the main branch${NC}"
    echo -e "${BLUE}Switching to main branch...${NC}"
    git checkout main
    git pull origin main
    CURRENT_BRANCH="main"
fi

echo -e "${GREEN}✅ Currently on main branch${NC}"
echo ""

# Check existing branches
echo -e "${BLUE}🔍 Checking existing branches...${NC}"
EXISTING_BRANCHES=$(git branch -a | grep -E "(main|develop|master)" | sed 's/^[* ]*//' | sed 's/remotes\/origin\///')

echo -e "${BLUE}Existing branches:${NC}"
echo "$EXISTING_BRANCHES"
echo ""

# Check if develop branch already exists
if echo "$EXISTING_BRANCHES" | grep -q "develop"; then
    echo -e "${GREEN}✅ Develop branch already exists${NC}"
    DEVELOP_EXISTS=true
else
    echo -e "${YELLOW}⚠️  Develop branch does not exist${NC}"
    DEVELOP_EXISTS=false
fi

# Function to create develop branch
create_develop_branch() {
    echo -e "${BLUE}🌿 Creating develop branch...${NC}"
    
    # Create and switch to develop branch
    git checkout -b develop
    
    # Push develop branch to remote
    git push -u origin develop
    
    echo -e "${GREEN}✅ Develop branch created and pushed to remote${NC}"
}

# Function to setup branch protection (if GitHub CLI is available)
setup_branch_protection() {
    if command -v gh &> /dev/null; then
        echo -e "${BLUE}🔒 Setting up branch protection rules...${NC}"
        
        # Get repository name
        REPO_URL=$(git remote get-url origin)
        REPO_NAME=$(basename -s .git "$REPO_URL")
        
        echo -e "${BLUE}Setting up protection for main branch...${NC}"
        gh api repos/:owner/:repo/branches/main/protection \
            --method PUT \
            --field required_status_checks='{"strict":true,"contexts":["Code Quality & Testing","Build Docker Images","Integration Testing"]}' \
            --field enforce_admins=true \
            --field required_pull_request_reviews='{"required_approving_review_count":1,"dismiss_stale_reviews":true}' \
            --field restrictions=null \
            --silent || echo -e "${YELLOW}⚠️  Could not set up main branch protection${NC}"
        
        echo -e "${BLUE}Setting up protection for develop branch...${NC}"
        gh api repos/:owner/:repo/branches/develop/protection \
            --method PUT \
            --field required_status_checks='{"strict":true,"contexts":["Code Quality & Testing","Build Docker Images","Integration Testing"]}' \
            --field enforce_admins=false \
            --field required_pull_request_reviews='{"required_approving_review_count":1,"dismiss_stale_reviews":true}' \
            --field restrictions=null \
            --silent || echo -e "${YELLOW}⚠️  Could not set up develop branch protection${NC}"
        
        echo -e "${GREEN}✅ Branch protection rules configured${NC}"
    else
        echo -e "${YELLOW}⚠️  GitHub CLI not found${NC}"
        echo -e "${BLUE}Please install GitHub CLI to set up branch protection:${NC}"
        echo -e "  https://cli.github.com/"
        echo ""
        echo -e "${BLUE}Or set up protection manually in GitHub:${NC}"
        echo -e "  Settings → Branches → Add rule"
    fi
}

# Function to create example feature branch
create_example_feature() {
    echo -e "${BLUE}🚀 Creating example feature branch...${NC}"
    
    # Switch to develop
    git checkout develop
    
    # Create example feature branch
    git checkout -b feature/example-feature
    
    # Create example file
    cat > EXAMPLE_FEATURE.md << 'EOF'
# Example Feature

This is an example feature branch to demonstrate the workflow.

## Development Workflow

1. **Create feature branch from develop**
   ```bash
   git checkout develop
   git pull origin develop
   git checkout -b feature/your-feature
   ```

2. **Develop and test locally**
   ```bash
   ./scripts/deploy-local.sh -d
   # Make your changes
   # Test locally
   docker-compose down
   ```

3. **Commit and push**
   ```bash
   git add .
   git commit -m "feat: your feature description"
   git push origin feature/your-feature
   ```

4. **Create Pull Request**
   - Go to GitHub
   - Create PR from feature/your-feature to develop
   - CI/CD automatically triggers

5. **After approval, merge to develop**
   - PR gets merged to develop
   - Automatically deploys to staging

6. **Deploy to production**
   ```bash
   git checkout main
   git merge develop
   git push origin main
   # Automatically deploys to production
   ```

## Branch Structure

```
main (production)
├── develop (staging)
    ├── feature/your-feature
    ├── feature/another-feature
    └── hotfix/urgent-fix
```

## Environment Mapping

- **feature/* branches** → Local development
- **develop branch** → Staging environment
- **main branch** → Production environment
EOF

    # Commit and push example feature
    git add EXAMPLE_FEATURE.md
    git commit -m "docs: add example feature workflow documentation"
    git push -u origin feature/example-feature
    
    echo -e "${GREEN}✅ Example feature branch created: feature/example-feature${NC}"
    
    # Switch back to develop
    git checkout develop
}

# Main execution
echo -e "${BLUE}🚀 Setting up branching strategy...${NC}"

# Create develop branch if it doesn't exist
if [[ "$DEVELOP_EXISTS" == false ]]; then
    create_develop_branch
else
    echo -e "${BLUE}Switching to existing develop branch...${NC}"
    git checkout develop
    git pull origin develop
fi

# Setup branch protection
setup_branch_protection

# Create example feature branch
create_example_feature

# Switch back to main
git checkout main

echo ""
echo -e "${GREEN}🎉 Branching strategy setup completed!${NC}"
echo ""

# Display current branch structure
echo -e "${BLUE}📊 Current Branch Structure:${NC}"
git branch -a | grep -E "(main|develop|feature)" | sed 's/^[* ]*//' | sed 's/remotes\/origin\///' | sort

echo ""
echo -e "${BLUE}🌿 Branching Strategy Summary:${NC}"
echo -e "  📍 ${GREEN}main${NC} → Production environment (protected)"
echo -e "  📍 ${GREEN}develop${NC} → Staging environment (protected)"
echo -e "  📍 ${GREEN}feature/*${NC} → Development branches"
echo -e "  📍 ${GREEN}hotfix/*${NC} → Emergency fixes (create from main)"

echo ""
echo -e "${BLUE}🚀 Next Steps:${NC}"
echo -e "  1. ${GREEN}Create feature branches from develop${NC}"
echo -e "  2. ${GREEN}Develop and test locally${NC}"
echo -e "  3. ${GREEN}Create PRs to develop for staging${NC}"
echo -e "  4. ${GREEN}Merge develop to main for production${NC}"

echo ""
echo -e "${BLUE}📚 Useful Commands:${NC}"
echo -e "  # Create feature branch"
echo -e "  git checkout develop && git pull origin develop"
echo -e "  git checkout -b feature/your-feature"
echo -e ""
echo -e "  # Deploy to staging (after PR merge to develop)"
echo -e "  ./scripts/deploy-ci-cd.sh -e staging -t rolling"
echo -e ""
echo -e "  # Deploy to production (after merge to main)"
echo -e "  ./scripts/deploy-ci-cd.sh -e production -t blue-green"

echo ""
echo -e "${GREEN}🎯 Your multi-environment CI/CD workflow is now ready!${NC}"
