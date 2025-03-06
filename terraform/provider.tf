terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"  # This allows any 5.x version
    }
  }
  required_version = ">= 0.14.9"
}

provider "aws" {
  region = var.aws_region
} 