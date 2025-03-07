#!/bin/bash
# Script to create ECR repositories for the Conversational Resume & Portfolio Chatbot

# Check if AWS CLI is installed
if ! command -v aws &> /dev/null
then
    echo "AWS CLI could not be found. Please install it first."
    exit 1
fi

# Check if jq is installed (for JSON parsing)
if ! command -v jq &> /dev/null
then
    echo "jq could not be found. Please install it first."
    exit 1
fi

# Ensure AWS CLI is configured
echo "Checking AWS CLI configuration..."
aws configure list

# Ask for confirmation
read -p "This will create ECR repositories in your AWS account. Continue? (y/n) " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]
then
    echo "Operation cancelled"
    exit 1
fi

# Set repository names
BACKEND_REPO="crpc-backend"
FRONTEND_REPO="crpc-frontend"

# Get AWS region from config
AWS_REGION=$(aws configure get region)
if [ -z "$AWS_REGION" ]
then
    read -p "AWS Region not found in config. Please enter your AWS region: " AWS_REGION
fi

echo "Creating ECR repositories in region $AWS_REGION..."

# Create backend repository
echo "Creating backend repository: $BACKEND_REPO"
BACKEND_RESULT=$(aws ecr create-repository --repository-name $BACKEND_REPO --region $AWS_REGION 2>&1)
if [[ $? -eq 0 ]]; then
    echo "Successfully created backend repository"
else
    if [[ $BACKEND_RESULT == *"RepositoryAlreadyExistsException"* ]]; then
        echo "Backend repository already exists, skipping"
    else
        echo "Error creating backend repository: $BACKEND_RESULT"
        exit 1
    fi
fi

# Create frontend repository
echo "Creating frontend repository: $FRONTEND_REPO"
FRONTEND_RESULT=$(aws ecr create-repository --repository-name $FRONTEND_REPO --region $AWS_REGION 2>&1)
if [[ $? -eq 0 ]]; then
    echo "Successfully created frontend repository"
else
    if [[ $FRONTEND_RESULT == *"RepositoryAlreadyExistsException"* ]]; then
        echo "Frontend repository already exists, skipping"
    else
        echo "Error creating frontend repository: $FRONTEND_RESULT"
        exit 1
    fi
fi

# Get account ID
ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)

# Print summary and next steps
echo ""
echo "==== SUMMARY ===="
echo "ECR repositories created successfully:"
echo "- $BACKEND_REPO: $ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/$BACKEND_REPO"
echo "- $FRONTEND_REPO: $ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/$FRONTEND_REPO"
echo ""
echo "==== NEXT STEPS ===="
echo "1. Add the following secrets to your GitHub repository:"
echo "   - AWS_ACCESS_KEY_ID: Your IAM user's access key"
echo "   - AWS_SECRET_ACCESS_KEY: Your IAM user's secret key"
echo "   - AWS_REGION: $AWS_REGION"
echo "   - ECR_BACKEND_REPOSITORY: $BACKEND_REPO"
echo "   - ECR_FRONTEND_REPOSITORY: $FRONTEND_REPO"
echo ""
echo "2. Push to your main branch to trigger the workflow or manually run it from the GitHub Actions tab" 