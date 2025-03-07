# GitHub Actions Workflows

This directory contains GitHub Actions workflow files that automate various processes for this repository.

## ECR Deployment Workflow (`ecr-deploy.yml`)

This workflow automatically builds and pushes Docker images to Amazon ECR when code is updated.

### Required GitHub Secrets

The following secrets must be configured in your GitHub repository settings:

| Secret Name | Description | Example Value |
|-------------|-------------|---------------|
| `AWS_ACCESS_KEY_ID` | IAM user's access key for ECR access | `AKIAIOSFODNN7EXAMPLE` |
| `AWS_SECRET_ACCESS_KEY` | IAM user's secret key for ECR access | `wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY` |
| `AWS_REGION` | AWS region where ECR repositories are located | `us-east-2` |
| `ECR_BACKEND_REPOSITORY` | Name of your backend ECR repository | `crpc-backend` |
| `ECR_FRONTEND_REPOSITORY` | Name of your frontend ECR repository | `crpc-frontend` |

### Setting Up Secrets

1. Go to your GitHub repository
2. Navigate to Settings > Secrets and variables > Actions
3. Click "New repository secret"
4. Add each of the above secrets with their actual values

### Workflow Behavior

The workflow:
- Triggers when code is pushed to the `main` branch (when changes affect backend, frontend, or Docker configuration)
- Builds Docker images for both the backend and frontend
- Tags images with both the commit SHA and `latest`
- Pushes the images to their respective ECR repositories
- Can be manually triggered using the GitHub Actions interface

### Important Notes

- Do not commit actual secret values to this repository
- Make sure your IAM user has the appropriate permissions for ECR operations
- The workflow will only run when relevant files are changed 