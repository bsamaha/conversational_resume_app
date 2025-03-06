# Output the instance ID
output "instance_id" {
  description = "The ID of the EC2 instance"
  value       = aws_spot_instance_request.app_instance.spot_instance_id
}

# Output the public IP
output "instance_public_ip" {
  description = "The public IP address of the EC2 instance"
  value       = aws_spot_instance_request.app_instance.public_ip
}

# Output the spot request ID
output "spot_request_id" {
  description = "The ID of the spot instance request"
  value       = aws_spot_instance_request.app_instance.id
}

# Output the S3 bucket name
output "s3_bucket_name" {
  description = "The name of the S3 bucket for chat logs (manually created)"
  value       = var.s3_bucket_name
}

# Output the application URL
output "application_url" {
  description = "The URL to access the application frontend"
  value       = "http://${aws_spot_instance_request.app_instance.public_ip}:3000"
}

# Output the AMI ID being used
output "ami_id" {
  description = "The AMI ID used for the EC2 instance"
  value       = var.ami_id != null ? var.ami_id : data.aws_ami.amazon_linux_2.id
}

# Output the AMI name (for the dynamically selected AMI)
output "ami_name" {
  description = "The name of the AMI used (if dynamically selected)"
  value       = var.ami_id == null ? data.aws_ami.amazon_linux_2.name : "Custom AMI specified"
} 