# Rebuilding the Conversational Resume Infrastructure

This guide will help you rebuild the EC2 instance and related infrastructure using Terraform while preserving your S3 data.

## Preserving Your S3 Data

**Important**: The S3 bucket and its data will be preserved because we've removed it from Terraform management. This ensures that your chat logs and other data remain intact between deployments.

## Using Your Existing S3 Bucket

This configuration is set up to use your manually created S3 bucket:
- Bucket name: `conversational-resume`
- Region: `us-east-2`
- ARN: `arn:aws:s3:::conversational-resume`

No additional setup is needed for the S3 bucket as it has already been manually created.

## Prerequisites

- Terraform installed on your local machine
- AWS CLI configured with appropriate credentials
- SSH key pair created in AWS (default name: `conversational_resume`)
- Your existing S3 bucket named `conversational-resume`
- ChromaDB data uploaded to the S3 bucket (instructions below)

## Preparing Your ChromaDB Data

Before rebuilding your infrastructure, you need to upload your ChromaDB data to your S3 bucket:

```bash
# On your local machine:
cd /path/to/your/project
zip -r chroma_data.zip data/chroma/

# Upload to S3 using AWS CLI
aws s3 cp chroma_data.zip s3://conversational-resume/
```

## Steps to Rebuild

1. **Navigate to the Terraform directory**:
   ```bash
   cd terraform
   ```

2. **Destroy existing infrastructure**:
   Since we've modified the `openai_api_key` variable to have a default empty value, you can run:
   ```bash
   terraform destroy
   ```
   Confirm with `yes` when prompted.
   
   If you're asked for the API key during destroy, you can provide any dummy value as it's not actually used during the destroy process:
   ```bash
   terraform destroy -var="openai_api_key=dummy_value"
   ```

3. **Initialize Terraform** (if needed):
   ```bash
   terraform init
   ```

4. **Apply the Terraform configuration**:
   ```bash
   terraform apply -var="openai_api_key=YOUR_ACTUAL_OPENAI_API_KEY"
   ```
   Replace `YOUR_ACTUAL_OPENAI_API_KEY` with your real OpenAI API key.
   
   Alternatively, you can export the variable:
   ```bash
   export TF_VAR_openai_api_key=YOUR_ACTUAL_OPENAI_API_KEY
   terraform apply
   ```
   
   Or create a terraform.tfvars file (based on terraform.tfvars.example):
   ```bash
   cp terraform.tfvars.example terraform.tfvars
   # Edit terraform.tfvars with your API key
   terraform apply
   ```

5. **Verify the application**:
   After the Terraform apply completes, it will output the public IP address of your EC2 instance.
   
   It will also output the S3 bucket name being used (`conversational-resume`), which should match your manually created bucket.
   
   Wait a few minutes for the application to start up, then check:
   - Frontend: `http://<ec2_public_ip>:3000`
   - Backend API: `http://<ec2_public_ip>:8000`

## Monitoring Deployment Progress

After applying the Terraform configuration, you can monitor the EC2 instance initialization and container setup:

1. **Connect to your EC2 instance**:
   ```bash
   ssh -i /path/to/your/key.pem ec2-user@<ec2_public_ip>
   ```

2. **View the cloud-init logs in real-time**:
   ```bash
   sudo tail -f /var/log/cloud-init-output.log
   ```
   This shows the progress of the user data script execution including:
   - Software installation
   - Repository cloning
   - Environment setup
   - Docker configuration
   - Container building and startup

3. **Monitor Docker build process**:
   When Docker Compose builds images, you can check the build process:
   ```bash
   # View all Docker processes (including builds)
   docker ps -a
   
   # Check build history
   docker image history backend
   docker image history frontend
   
   # View Docker events in real-time
   docker events
   ```

4. **Monitor Docker container logs**:
   ```bash
   # View logs for all containers
   docker-compose logs
   
   # Follow logs in real-time
   docker-compose logs -f
   
   # View logs for specific container
   docker-compose logs backend
   docker-compose logs frontend
   ```

5. **Check system resource usage**:
   ```bash
   # Monitor CPU and memory usage
   top
   
   # Docker-specific resource usage
   docker stats
   ```

The full initialization process typically takes 5-10 minutes depending on network speed and instance type.

## Troubleshooting

If the application doesn't start properly:

1. **SSH into the instance**:
   ```bash
   ssh -i /path/to/your/key.pem ec2-user@<ec2_public_ip>
   ```

2. **Check Docker logs**:
   ```bash
   docker ps
   docker logs backend
   docker logs frontend
   ```

3. **Check user data script execution**:
   ```bash
   sudo cat /var/log/cloud-init-output.log
   ```

4. **Manually restart the containers** (if needed):
   ```bash
   cd ~/conversational-resume
   docker-compose down
   docker-compose up -d
   ```

## Common Issues

### Terraform Interpolation Syntax
- The special characters in bash scripts (like `$`) need to be escaped for Terraform
- If you see errors about invalid references, make sure to double the dollar signs (`$$`) in shell scripts
- Example: `${variable}` in a shell script should be written as `$${variable}` in Terraform's user_data

### Docker Configuration
- If Docker fails to start with errors about invalid characters in daemon.json file, the issue may be related to how the configuration file is created in the user_data script
- The heredoc approach (`cat > file << 'EOF'`) is preferred over `echo` with escape sequences when creating configuration files
- Check the logs with `sudo journalctl -u docker --no-pager` to diagnose Docker startup issues

### Network Connectivity Issues
- If you see errors like `Failed to establish a new connection: [Errno -2] Name or service not known` in the build logs, your instance is experiencing DNS resolution problems
- This commonly happens when the Docker build process can't connect to package repositories

To fix network connectivity issues:

1. **Check DNS configuration**:
   ```bash
   cat /etc/resolv.conf
   ```

2. **Test basic connectivity**:
   ```bash
   ping -c 4 8.8.8.8        # Test basic internet connectivity
   ping -c 4 pypi.org       # Test DNS resolution to Python package repository
   ```

3. **Add public DNS servers** (if needed):
   ```bash
   sudo sh -c 'echo "nameserver 8.8.8.8" >> /etc/resolv.conf'
   sudo sh -c 'echo "nameserver 1.1.1.1" >> /etc/resolv.conf'
   ```

4. **Configure Docker to use specific DNS**:
   ```bash
   sudo mkdir -p /etc/docker
   sudo sh -c 'cat > /etc/docker/daemon.json << EOF
{
  "default-shm-size": "1G",
  "dns": ["8.8.8.8", "1.1.1.1"]
}
EOF'
   sudo systemctl restart docker
   ```

5. **Check for problematic package repository URLs**:
   If you're still having issues, check the Dockerfile for potentially unreachable package sources:
   ```bash
   cat backend/Dockerfile | grep -i "ENV PIP"
   ```
   
   Remove or comment out problematic URLs (especially mirrors from other regions):
   ```bash
   sudo sed -i 's/ENV PIP_FIND_LINKS=/#ENV PIP_FIND_LINKS=/g' backend/Dockerfile
   ```

6. **Retry the build process**:
   ```bash
   cd ~/conversational-resume
   docker-compose down
   docker-compose build --no-cache
   docker-compose up -d
   ```

## Setting Up Required Data

The infrastructure now has improved automation:

1. **AWS Credentials**: The application now uses an IAM role attached to the EC2 instance
   - No need to manually configure AWS credentials
   - The EC2 instance has permissions to access your S3 bucket automatically
   - More secure than hardcoded credentials

2. **ChromaDB Data**: The application automatically downloads ChromaDB data from your S3 bucket
   - During instance initialization, ChromaDB data is downloaded from S3
   - Make sure you've uploaded `chroma_data.zip` to your S3 bucket before applying Terraform
   - The setup process is now fully automated

If you still encounter issues after rebuilding:

1. **Verify IAM role assignment**:
   ```bash
   # SSH into your instance
   ssh -i /path/to/your/key.pem ec2-user@<ec2_public_ip>
   
   # Check if the instance has the correct IAM role
   curl http://169.254.169.254/latest/meta-data/iam/security-credentials/
   ```

2. **Check if ChromaDB data was downloaded correctly**:
   ```bash
   cd ~/conversational-resume
   ls -la data/chroma
   ```

3. **Restart the Docker containers** (if needed):
   ```bash
   cd ~/conversational-resume
   docker-compose down
   docker-compose up -d
   ``` 