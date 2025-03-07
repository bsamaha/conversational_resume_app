#!/bin/bash
# Script to set up Parameter Store secrets for the Conversational Resume & Portfolio Chatbot

# Check if AWS CLI is installed
if ! command -v aws &> /dev/null
then
    echo "AWS CLI could not be found. Please install it first."
    exit 1
fi

# Ensure AWS CLI is configured
echo "Checking AWS CLI configuration..."
aws configure list

# Default region
AWS_REGION=$(aws configure get region)
if [ -z "$AWS_REGION" ]
then
    read -p "AWS Region not found in config. Please enter your AWS region: " AWS_REGION
fi

# Ask for confirmation
read -p "This will create or update parameters in AWS Parameter Store. Continue? (y/n) " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]
then
    echo "Operation cancelled"
    exit 1
fi

# Ask for the secrets
read -p "Enter your OpenAI API key: " OPENAI_API_KEY
read -p "Enter your AWS access key ID for the application: " AWS_ACCESS_KEY_ID
read -p "Enter your AWS secret access key for the application: " AWS_SECRET_ACCESS_KEY

# Store OpenAI API key
echo "Storing OpenAI API key in Parameter Store..."
aws ssm put-parameter \
    --name "OPENAI_API_KEY" \
    --value "$OPENAI_API_KEY" \
    --type "SecureString" \
    --overwrite \
    --region "$AWS_REGION"

if [ $? -ne 0 ]; then
    echo "Failed to store OpenAI API key"
    exit 1
fi

# Store AWS credentials
echo "Storing AWS access key ID in Parameter Store..."
aws ssm put-parameter \
    --name "CONVERSATIONAL_RESUME_AWS_ACCESS_KEY_ID" \
    --value "$AWS_ACCESS_KEY_ID" \
    --type "SecureString" \
    --overwrite \
    --region "$AWS_REGION"

if [ $? -ne 0 ]; then
    echo "Failed to store AWS access key ID"
    exit 1
fi

echo "Storing AWS secret access key in Parameter Store..."
aws ssm put-parameter \
    --name "CONVERSATIONAL_RESUME_AWS_ACCESS_KEY_SECRET" \
    --value "$AWS_SECRET_ACCESS_KEY" \
    --type "SecureString" \
    --overwrite \
    --region "$AWS_REGION"

if [ $? -ne 0 ]; then
    echo "Failed to store AWS secret access key"
    exit 1
fi

# Create IAM policy (optional)
echo "Would you like to create an IAM policy for Parameter Store access? (y/n) "
read -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]
then
    POLICY_NAME="ParameterStoreReadAccess"
    POLICY_DOC='{
        "Version": "2012-10-17",
        "Statement": [
            {
                "Effect": "Allow",
                "Action": [
                    "ssm:GetParameter",
                    "ssm:GetParameters"
                ],
                "Resource": "arn:aws:ssm:'$AWS_REGION':'$(aws sts get-caller-identity --query Account --output text)':parameter/*"
            }
        ]
    }'
    
    echo "Creating IAM policy $POLICY_NAME..."
    aws iam create-policy \
        --policy-name "$POLICY_NAME" \
        --policy-document "$POLICY_DOC" \
        --region "$AWS_REGION"
    
    if [ $? -ne 0 ]; then
        echo "Failed to create IAM policy, but parameters were stored successfully"
    else
        echo "IAM policy created successfully"
    fi
fi

# Print summary
echo ""
echo "==== SUMMARY ===="
echo "Parameters created successfully in region $AWS_REGION:"
echo "- OPENAI_API_KEY"
echo "- CONVERSATIONAL_RESUME_AWS_ACCESS_KEY_ID"
echo "- CONVERSATIONAL_RESUME_AWS_ACCESS_KEY_SECRET"
echo ""
echo "To verify, run:"
echo "aws ssm get-parameters --names \"OPENAI_API_KEY\" \"CONVERSATIONAL_RESUME_AWS_ACCESS_KEY_ID\" \"CONVERSATIONAL_RESUME_AWS_ACCESS_KEY_SECRET\" --with-decryption --region $AWS_REGION"
echo ""
echo "Your application should now be able to access these secrets when running in production mode." 