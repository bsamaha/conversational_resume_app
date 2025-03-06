# Deployment Guide for Conversational Resume

This guide provides a step-by-step process for deploying your Conversational Resume application using Terraform.

## Prerequisites

Before starting the deployment, ensure you have:

1. **AWS Account and CLI**
   - AWS CLI installed and configured with admin privileges
   - Run `aws configure` to set up your credentials if not already done

2. **Terraform**
   - Terraform CLI installed (v1.0.0+)
   - Verify with `terraform --version`

3. **SSH Key Pair**
   - Create an AWS key pair: 
     ```bash
     aws ec2 create-key-pair --key-name conversational_resume --query 'KeyMaterial' --output text > conversational_resume.pem
     chmod 400 conversational_resume.pem
     ```

4. **Existing S3 Bucket**
   - Confirm your S3 bucket exists and contains the Chroma data:
     ```bash
     aws s3 ls s3://your-bucket-name/
     ```

5. **IAM Role Configuration**
   - We're using an existing IAM role named "EC2S3AccessRole" with AmazonS3FullAccess policy
   - No additional role setup is required

## Step 1: Ensure IAM Instance Profile Exists

The Terraform configuration uses the existing IAM role "EC2S3AccessRole". Make sure the role has an instance profile:

1. Check if an instance profile exists for the role:
   ```bash
   aws iam list-instance-profiles-for-role --role-name EC2S3AccessRole
   ```

2. If no instance profile exists, create one:
   ```bash
   aws iam create-instance-profile --instance-profile-name EC2S3AccessRole
   aws iam add-role-to-instance-profile --instance-profile-name EC2S3AccessRole --role-name EC2S3AccessRole
   ```

## Step 2: Configure Terraform Variables

1. Create your `terraform.tfvars` file:
   ```bash
   cp terraform.tfvars.example terraform.tfvars
   ```

2. Edit `terraform.tfvars` to update:
   - `openai_api_key`: Your OpenAI API key
   - `s3_bucket_name`: Your existing S3 bucket name
   - `key_name`: Your SSH key pair name (default: conversational_resume)
   - `aws_region`: AWS region where your bucket is located

## Step 3: Deploy the Infrastructure

1. Initialize Terraform:
   ```bash
   terraform init
   ```

2. Validate your configuration:
   ```bash
   terraform validate
   ```

3. Preview the changes:
   ```bash
   terraform plan
   ```

4. Deploy the infrastructure:
   ```bash
   terraform apply
   ```

5. Note the outputs, especially the EC2 instance's public IP

## Step 4: Verify the Deployment

1. Wait for user_data script to complete (typically 5-10 minutes)

2. SSH into the instance to check progress:
   ```bash
   ssh -i conversational_resume.pem ec2-user@<ec2-public-ip>
   ```

3. Check initialization progress:
   ```bash
   sudo tail -f /var/log/cloud-init-output.log
   ```

4. Verify Docker containers are running:
   ```bash
   docker ps
   ```

5. Check S3 access is working:
   ```bash
   aws s3 ls s3://your-bucket-name/
   ```

6. Access your application in a browser:
   - Frontend: `http://<ec2-public-ip>:3000`
   - Backend API: `http://<ec2-public-ip>:8000`

## Troubleshooting Common Issues

### S3 Access Issues

If your application can't access the S3 bucket:

1. Check IAM role/profile is correctly attached:
   ```bash
   aws ec2 describe-instances --instance-ids <instance-id> --query 'Reservations[0].Instances[0].IamInstanceProfile'
   ```

2. Verify EC2S3AccessRole permissions:
   ```bash
   aws iam get-role-policy --role-name EC2S3AccessRole --policy-name AmazonS3FullAccess
   ```
   
   If you don't see the policy, it might be an AWS managed policy. Check attached policies:
   ```bash
   aws iam list-attached-role-policies --role-name EC2S3AccessRole
   ```

3. Test S3 access manually from the EC2 instance:
   ```bash
   aws s3 ls s3://your-bucket-name/
   ```

### Application Startup Issues

If containers don't start properly:

1. Check Docker logs:
   ```bash
   docker-compose logs
   ```

2. Restart the containers:
   ```bash
   cd ~/conversational-resume
   docker-compose down
   docker-compose up -d
   ```

3. Check for errors in user_data execution:
   ```bash
   sudo cat /var/log/cloud-init-output.log
   ```

## Maintenance

### Updating the Application

To update your application:

1. SSH into the instance
2. Pull latest changes:
   ```bash
   cd ~/conversational-resume
   git pull
   ```
3. Rebuild and restart containers:
   ```bash
   docker-compose down
   docker-compose up -d --build
   ```

### Backing Up Data

To back up your ChromaDB data:

```bash
cd ~/conversational-resume
zip -r chroma_backup.zip data/chroma/
aws s3 cp chroma_backup.zip s3://your-bucket-name/backups/chroma_backup_$(date +%Y%m%d).zip
```

## Cleanup

To destroy all resources when you're done:

```bash
terraform destroy
```

Note: This will not delete your manually created S3 bucket or IAM role. 