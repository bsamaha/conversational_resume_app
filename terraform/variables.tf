variable "aws_region" {
  description = "The AWS region to deploy resources in"
  type        = string
  default     = "us-east-2"
}

variable "ami_id" {
  description = "Optional: The Amazon Machine Image ID to use for the EC2 instance (if not specified, the latest Amazon Linux 2 AMI will be used)"
  type        = string
  default     = null  # Set to null so the data source is used by default
}

variable "instance_type" {
  description = "The EC2 instance type"
  type        = string
  default     = "t2.small"
}

variable "max_spot_price" {
  description = "The maximum spot price you are willing to pay"
  type        = string
  default     = "0.02"  # Adjust based on your budget
}

variable "key_name" {
  description = "The name of the SSH key pair to use"
  type        = string
  # You'll need to create this key pair in the AWS console
  default     = "conversational_resume"
}

variable "repo_url" {
  description = "The Git repository URL to clone"
  type        = string
  # Update this with your actual repository URL
  default     = "https://github.com/bsamaha/converstaional_resume"
}

variable "s3_bucket_name" {
  description = "The name for the S3 bucket to store chat logs"
  type        = string
  default     = "conversational-resume"
}

variable "environment" {
  description = "The environment (e.g., dev, prod)"
  type        = string
  default     = "prod"
}

variable "openai_api_key" {
  description = "Your OpenAI API key (sensitive)"
  type        = string
  sensitive   = true
  # Empty default so it's optional for terraform destroy
  default     = ""
} 