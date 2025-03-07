#!/bin/bash
# Script to log in to ECR and pull images
# Usage: ./ecr-login-pull.sh [aws-region] [aws-profile]
#        ./ecr-login-pull.sh --profile profilename

set -e

# Parse command line arguments
AWS_REGION="us-east-2"  # Default region
AWS_PROFILE="default"   # Default profile

# Check if arguments are provided in --param format
while [[ $# -gt 0 ]]; do
  case "$1" in
    --region)
      AWS_REGION="$2"
      shift 2
      ;;
    --profile)
      AWS_PROFILE="$2"
      shift 2
      ;;
    *)
      # Legacy positional arguments
      if [ -z "$POSITIONAL_ARG1" ]; then
        POSITIONAL_ARG1="$1"
        shift
      elif [ -z "$POSITIONAL_ARG2" ]; then
        POSITIONAL_ARG2="$1"
        shift
      else
        echo "Unknown argument: $1"
        exit 1
      fi
      ;;
  esac
done

# Support legacy positional arguments
[ -n "$POSITIONAL_ARG1" ] && AWS_REGION="$POSITIONAL_ARG1"
[ -n "$POSITIONAL_ARG2" ] && AWS_PROFILE="$POSITIONAL_ARG2"

# Load environment variables from .env file more safely
if [ -f ".env" ]; then
    echo "Loading environment variables from .env file"
    # Only export lines that contain KEY=VALUE format and don't start with #
    while IFS= read -r line || [[ -n "$line" ]]; do
        # Skip empty lines and comment lines
        if [[ -z "$line" || "$line" =~ ^[[:space:]]*# ]]; then
            continue
        fi
        # Export the variable if it's in KEY=VALUE format, trim whitespace
        if [[ "$line" =~ ^[[:alpha:]][[:alnum:]_]*= ]]; then
            # Extract just the variable name
            varname=$(echo "$line" | cut -d= -f1)
            # Extract the value and remove any trailing/leading whitespace
            varvalue=$(echo "$line" | cut -d= -f2- | sed 's/^[[:space:]]*//;s/[[:space:]]*$//')
            # Export the trimmed variable
            export "$varname=$varvalue"
        fi
    done < .env
else
    echo "No .env file found. Please create one based on .env.example"
    exit 1
fi

# Extremely aggressive whitespace removal
strip_all_whitespace() {
    echo "$1" | tr -d '[:space:]'
}

# Trim any whitespace from variables (using multiple methods to be sure)
AWS_ACCOUNT_ID=$(strip_all_whitespace "$AWS_ACCOUNT_ID")
ECR_BACKEND_REPOSITORY=$(strip_all_whitespace "$ECR_BACKEND_REPOSITORY")
ECR_FRONTEND_REPOSITORY=$(strip_all_whitespace "$ECR_FRONTEND_REPOSITORY")

if [ -z "$AWS_ACCOUNT_ID" ] || [ -z "$ECR_BACKEND_REPOSITORY" ] || [ -z "$ECR_FRONTEND_REPOSITORY" ]; then
    echo "Required environment variables not set. Please check your .env file."
    echo "Required: AWS_ACCOUNT_ID, ECR_BACKEND_REPOSITORY, ECR_FRONTEND_REPOSITORY"
    exit 1
fi

# Make ECR URL with guaranteed no whitespace
ECR_URL="$(strip_all_whitespace "${AWS_ACCOUNT_ID}").dkr.ecr.${AWS_REGION}.amazonaws.com"

echo "Logging in to Amazon ECR in region $AWS_REGION using profile $AWS_PROFILE..."
echo "Using AWS account ID: '$AWS_ACCOUNT_ID'"
echo "ECR URL: '$ECR_URL'"

# Try to get ECR auth token - handle expired credentials
if ! PASSWORD=$(aws ecr get-login-password --region "$AWS_REGION" --profile "$AWS_PROFILE" 2>&1); then
    echo "Error getting ECR login credentials. Please check your AWS credentials."
    echo "If your token has expired, please run: aws sso login --profile $AWS_PROFILE"
    echo "Error details:"
    echo "$PASSWORD"
    exit 1
fi

# Use the password with docker login
echo "$PASSWORD" | docker login --username AWS --password-stdin "$ECR_URL"

echo "Pulling backend image..."
docker pull "${ECR_URL}/${ECR_BACKEND_REPOSITORY}:latest"

echo "Pulling frontend image..."
docker pull "${ECR_URL}/${ECR_FRONTEND_REPOSITORY}:latest"

echo "Images pulled successfully. You can now run: docker-compose up" 