# Conversational Resume Infrastructure Deployment Plan

This Terraform configuration sets up the complete infrastructure for running your Conversational Resume application on AWS EC2 spot instances. This document outlines the deployment strategy, prerequisites, and implementation details.

## Infrastructure Overview

The deployment creates and manages:
- EC2 spot instance running Docker and Docker Compose
- Security groups for proper network access
- Uses an existing IAM role (EC2S3AccessRole) for EC2 to access S3
- Uses an existing S3 bucket for storing ChromaDB data and chat logs

## Architecture Diagram

```
┌─────────────────┐     ┌────────────────┐     ┌───────────────┐
│                 │     │                │     │               │
│  EC2 Instance   │────▶│  Application   │────▶│   S3 Bucket   │
│  (Docker)       │     │  Containers    │     │  (Data Store) │
│                 │     │                │     │               │
└─────────────────┘     └────────────────┘     └───────────────┘
        ▲                                              ▲
        │                                              │
        └──────────────────────────────────────────────┘
              IAM Role-based Access (EC2S3AccessRole)
```

## S3 Access Strategy

The application accesses the S3 bucket using:

### IAM Role-based Access (Implemented)
- Using existing IAM role "EC2S3AccessRole" with AmazonS3FullAccess policy
- The role is attached to the EC2 instance via its instance profile
- The application uses the instance profile credentials automatically through the AWS SDK

## Prerequisites

Before deploying with Terraform, you need:

1. **AWS Account and CLI Setup**
   - [AWS CLI](https://aws.amazon.com/cli/) installed and configured with your credentials
   - Administrator access to create EC2 and other resources

2. **Terraform Installation**
   - [Terraform](https://www.terraform.io/downloads.html) v1.0.0+ installed

3. **SSH Key Pair**
   - Create an SSH key pair in your AWS account (default name: `conversational_resume`)
   - This will be used to access the EC2 instance if needed

4. **S3 Bucket Setup**
   - Your existing S3 bucket with the ChromaDB data already uploaded
   - The bucket name should be specified in your terraform.tfvars file

5. **IAM Role Configuration**
   - We're using the existing IAM role "EC2S3AccessRole" with AmazonS3FullAccess policy
   - Ensure the role has an instance profile with the same name

## Deployment Steps

1. **Configure Variables**
   - Copy `terraform.tfvars.example` to `terraform.tfvars`
   - Update the variables:
     - `openai_api_key`: Your OpenAI API key
     - `s3_bucket_name`: Your existing S3 bucket name
     - `key_name`: Your SSH key pair name
     - Update other variables as needed

2. **Initialize Terraform**
   ```bash
   terraform init
   ```

3. **Deploy the Infrastructure**
   ```bash
   terraform apply
   ```

4. **Verify Deployment**
   - Check the outputs for EC2 instance IP
   - Access your application at `http://<ec2_public_ip>:3000`

## Post-Deployment Verification

1. **Check S3 Access**
   - SSH into the EC2 instance: `ssh -i <your-key.pem> ec2-user@<ec2-ip>`
   - Verify S3 access: `aws s3 ls s3://<your-bucket-name>`

2. **Verify Application Logs**
   - Check Docker logs: `docker-compose logs`
   - Monitor S3 access: `tail -f /var/log/cloud-init-output.log`

## Troubleshooting

If you encounter issues with S3 access:

1. **Check IAM Role Configuration**
   - Verify the role exists and has the AmazonS3FullAccess policy
   - Ensure the instance profile exists and is correctly attached

2. **Network Connectivity**
   - Check if the EC2 instance can reach S3: `curl -v https://<your-bucket-name>.s3.<region>.amazonaws.com`

## Cleaning Up

To destroy all resources when you're done:

```bash
terraform destroy
```

**Note**: This will not delete your manually created S3 bucket or IAM role.

## Security Considerations

- The configuration uses SSH key authentication for EC2 access
- Security groups limit access to necessary ports only
- The AmazonS3FullAccess policy provides broad permissions - consider restricting to specific buckets in production
- Consider enabling S3 bucket encryption for sensitive data 