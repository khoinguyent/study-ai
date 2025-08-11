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
