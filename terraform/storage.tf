# S3 bucket resources are commented out because we're using an existing manually created bucket
# We're using the IAM Role-based access approach with the existing "EC2S3AccessRole"

# Current S3 Access Configuration:
# - Using existing IAM role "EC2S3AccessRole" with AmazonS3FullAccess policy
# - This role is attached to the EC2 instance via the instance profile
# - The application will use these credentials automatically via the AWS SDK

# Option 1: IAM Role-based Access (IMPLEMENTED)
# - Using existing IAM role "EC2S3AccessRole" with AmazonS3FullAccess policy
# - This role is attached to the EC2 instance in main.tf
# - The application will use the instance profile credentials automatically

# Option 2: Environment Variables (ALTERNATIVE)
# - Not being used since we're using IAM roles
# - Would require environment variables in the .env file:
#   - AWS_ACCESS_KEY_ID
#   - AWS_SECRET_ACCESS_KEY
#   - AWS_REGION
#   - AWS_S3_BUCKET_NAME (set to ${var.s3_bucket_name})

/*
# Only uncomment this if you want to manage the S3 bucket through Terraform
# Warning: This may delete your existing bucket and data if resource already exists with this name

# S3 bucket for storing application data
resource "aws_s3_bucket" "app_data" {
  bucket = var.s3_bucket_name
  
  tags = {
    Name        = "Conversational Resume App Data"
    Environment = var.environment
  }
}

# S3 bucket ownership controls
resource "aws_s3_bucket_ownership_controls" "app_data_ownership" {
  bucket = aws_s3_bucket.app_data.id
  
  rule {
    object_ownership = "BucketOwnerPreferred"
  }
}

# S3 bucket server-side encryption
resource "aws_s3_bucket_server_side_encryption_configuration" "app_data_encryption" {
  bucket = aws_s3_bucket.app_data.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}
*/

# IMPORTANT NOTE:
# We're using the existing "EC2S3AccessRole" with AmazonS3FullAccess policy
# This provides full access to all S3 buckets - consider restricting permissions in production
# for better security by limiting access to only the specific bucket needed 