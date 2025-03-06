# Data source to get the latest Amazon Linux 2 AMI
data "aws_ami" "amazon_linux_2" {
  most_recent = true
  owners      = ["amazon"]

  filter {
    name   = "name"
    values = ["amzn2-ami-hvm-*-x86_64-gp2"]
  }

  filter {
    name   = "virtualization-type"
    values = ["hvm"]
  }
  
  filter {
    name   = "root-device-type"
    values = ["ebs"]
  }
  
  filter {
    name   = "state"
    values = ["available"]
  }
}

# Security group for your application
resource "aws_security_group" "app_sg" {
  name        = "conversational-resume-sg"
  description = "Security group for conversational resume application"

  # Allow HTTP and HTTPS traffic
  ingress {
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  ingress {
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  # Allow traffic to your backend port (8000)
  ingress {
    from_port   = 8000
    to_port     = 8000
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  # Allow traffic to your frontend port (3000)
  ingress {
    from_port   = 3000
    to_port     = 3000
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  # Allow SSH access
  ingress {
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  # Allow all outbound traffic
  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
}

# EC2 spot instance request
resource "aws_spot_instance_request" "app_instance" {
  ami                    = var.ami_id != null ? var.ami_id : data.aws_ami.amazon_linux_2.id
  instance_type          = var.instance_type
  spot_price             = var.max_spot_price
  spot_type              = "persistent"
  wait_for_fulfillment   = true
  key_name               = var.key_name
  vpc_security_group_ids = [aws_security_group.app_sg.id]
  # Using existing EC2S3AccessRole via an instance profile
  iam_instance_profile   = "EC2S3AccessRole"

  tags = {
    Name = "ConversationalResume-SpotInstance"
  }

  user_data = <<-EOF
    #!/bin/bash
    set -e
    
    # Update system packages
    yum update -y
    
    # Install required packages
    yum install -y docker git wget unzip aws-cli
    
    # Start and enable Docker
    systemctl start docker
    systemctl enable docker
    
    # Add ec2-user to docker group
    usermod -aG docker ec2-user
    
    # Install Docker Compose
    curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
    chmod +x /usr/local/bin/docker-compose
    ln -sf /usr/local/bin/docker-compose /usr/bin/docker-compose
    
    # Create app directory
    mkdir -p /home/ec2-user/conversational-resume
    cd /home/ec2-user/conversational-resume
    
    # Instead of cloning a repo, just create the required directories and files
    mkdir -p backend frontend data/chroma
    
    # Create a basic docker-compose.yml file
    cat > docker-compose.yml << 'DOCKER_COMPOSE'
services:
  backend:
    build: 
      context: ./backend
      dockerfile: Dockerfile
    container_name: backend
    volumes:
      - ./data/chroma:/app/data/chroma
    env_file:
      - .env
    environment:
      - CHROMA_DB_PATH=/app/data/chroma
      - OPENAI_API_KEY=${OPENAI_API_KEY}
      - AWS_ACCESS_KEY_ID=${AWS_ACCESS_KEY_ID}
      - AWS_SECRET_ACCESS_KEY=${AWS_SECRET_ACCESS_KEY}
      - AWS_S3_BUCKET_NAME=${AWS_S3_BUCKET_NAME}
      - AWS_REGION=${AWS_REGION}
    restart: unless-stopped
    networks:
      - app-network
    ports:
      - "8000:8000"
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 30s

  frontend:
    build: ./frontend
    container_name: frontend
    restart: unless-stopped
    ports:
      - "3000:80"
    environment:
      - REACT_APP_API_URL=http://backend:8000
    depends_on:
      backend:
        condition: service_healthy
    networks:
      - app-network

networks:
  app-network:
    driver: bridge
DOCKER_COMPOSE
    
    # Download the pre-built app files from S3 instead of using Git
    echo "Downloading application files from S3..."
    aws s3 cp s3://${var.s3_bucket_name}/app_files.zip /tmp/app_files.zip || echo "No app_files.zip found, continuing setup"
    
    # Try to extract app files if they exist
    if [ -f "/tmp/app_files.zip" ]; then
      echo "Extracting application files..."
      unzip -o /tmp/app_files.zip -d /home/ec2-user/conversational-resume/
    else
      echo "Creating basic app structures..."
      # Create basic app structures, will use uploaded data for the DB
      mkdir -p backend/app
      mkdir -p frontend/public
    fi
    
    # Create a basic .env file if not already existing
    if [ ! -f ".env" ]; then
      cat > .env << 'ENV_FILE'
OPENAI_API_KEY=${var.openai_api_key}
CHROMA_DB_PATH=/app/data/chroma
AWS_ACCESS_KEY_ID=${AWS_ACCESS_KEY_ID}
AWS_SECRET_ACCESS_KEY=${AWS_SECRET_ACCESS_KEY}
AWS_S3_BUCKET_NAME=${var.s3_bucket_name}
AWS_REGION=${var.aws_region}
ENV_FILE
    fi
    
    # Update .env file with proper configuration
    sed -i "s|OPENAI_API_KEY=.*|OPENAI_API_KEY=${var.openai_api_key}|" .env
    sed -i "s|CHROMA_DB_PATH=.*|CHROMA_DB_PATH=/app/data/chroma|" .env
    sed -i "s|AWS_S3_BUCKET_NAME=.*|AWS_S3_BUCKET_NAME=${var.s3_bucket_name}|" .env
    sed -i "s|AWS_REGION=.*|AWS_REGION=${var.aws_region}|" .env
    
    # Create proper directories for ChromaDB data
    mkdir -p /home/ec2-user/conversational-resume/data/chroma
    
    # Download ChromaDB data from S3 bucket
    echo "Downloading ChromaDB data from S3..."
    aws s3 cp s3://${var.s3_bucket_name}/chroma_data.zip /tmp/chroma_data.zip
    
    # Extract data with proper structure preservation and destination
    echo "Extracting ChromaDB data..."
    unzip -o /tmp/chroma_data.zip -d /tmp/chroma_extract
    
    # Move the data to the correct location, ensuring we get the right structure
    echo "Setting up ChromaDB data in the correct location..."
    if [ -d "/tmp/chroma_extract/data/chroma" ]; then
      # If the zip contains data/chroma structure, copy that
      cp -r /tmp/chroma_extract/data/chroma/* /home/ec2-user/conversational-resume/data/chroma/
    elif [ -d "/tmp/chroma_extract/chroma" ]; then
      # If the zip contains just chroma directory
      cp -r /tmp/chroma_extract/chroma/* /home/ec2-user/conversational-resume/data/chroma/
    else
      # If the zip directly contains the chroma files
      cp -r /tmp/chroma_extract/* /home/ec2-user/conversational-resume/data/chroma/
    fi
    
    # Set proper permissions
    chown -R ec2-user:ec2-user /home/ec2-user/conversational-resume/data
    chmod -R 755 /home/ec2-user/conversational-resume/data
    
    # Verify data was extracted properly
    echo "Verifying ChromaDB data..."
    ls -la /home/ec2-user/conversational-resume/data/chroma/
    
    # Modify docker-compose.yml to correctly map the volume
    echo "Updating docker-compose.yml volume mapping..."
    sed -i 's|\.\/chroma:/app/data/chroma|\.\/data/chroma:/app/data/chroma|g' docker-compose.yml
    
    # Apply optimization fixes to Dockerfile before building
    # Update backend Dockerfile to prefer binary packages
    sed -i '2a ENV PIP_PREFER_BINARY=1\nENV PIP_EXTRA_INDEX_URL=https://pypi.org/simple\nENV PYTHONDONTWRITEBYTECODE=1\nENV PYTHONUNBUFFERED=1' backend/Dockerfile
    
    # Update pip install command to use --prefer-binary
    sed -i 's/pip install --no-cache-dir/pip install --prefer-binary --no-cache-dir/g' backend/Dockerfile
    
    # Increase Docker's memory limit (EC2 has more RAM than most dev machines)
    mkdir -p /etc/docker
    cat > /etc/docker/daemon.json << 'DOCKER_CONFIG'
{
  "default-shm-size": "1G",
  "dns": ["8.8.8.8", "1.1.1.1"]
}
DOCKER_CONFIG
    systemctl restart docker
    
    # Ensure all environment variables are correctly passed to containers
    sed -i '/environment:/a \ \ \ \ \ \ - OPENAI_API_KEY=$${OPENAI_API_KEY}' docker-compose.yml
    sed -i '/OPENAI_API_KEY=/a \ \ \ \ \ \ - AWS_ACCESS_KEY_ID=$${AWS_ACCESS_KEY_ID}' docker-compose.yml
    sed -i '/AWS_ACCESS_KEY_ID=/a \ \ \ \ \ \ - AWS_SECRET_ACCESS_KEY=$${AWS_SECRET_ACCESS_KEY}' docker-compose.yml
    sed -i '/AWS_SECRET_ACCESS_KEY=/a \ \ \ \ \ \ - AWS_REGION=$${AWS_REGION}' docker-compose.yml
    sed -i '/AWS_REGION=/a \ \ \ \ \ \ - AWS_S3_BUCKET_NAME=$${AWS_S3_BUCKET_NAME}' docker-compose.yml
    
    # Set more memory for Docker Compose
    export DOCKER_OPTS="-m 4G"
    
    # Start the application
    echo "Starting Docker containers..."
    docker-compose up -d
    
    echo "Setup complete! The application should now be running with proper ChromaDB data."
  EOF

  # Request a persistent spot instance that won't terminate when spot price changes
  instance_interruption_behavior = "stop"
}

# Using existing EC2S3AccessRole for S3 access
# The IAM role "EC2S3AccessRole" with AmazonS3FullAccess policy has been manually created
# No need to uncomment or create additional IAM resources
/*
# IAM role for EC2 to access S3
resource "aws_iam_role" "ec2_s3_access_role" {
  name = "ec2_s3_access_role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "ec2.amazonaws.com"
        }
      },
    ]
  })

  tags = {
    Name = "EC2S3AccessRole"
  }
}

# IAM policy for S3 access
resource "aws_iam_policy" "s3_access_policy" {
  name        = "s3_access_policy"
  description = "Policy for EC2 to access specific S3 bucket"

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = [
          "s3:GetObject",
          "s3:PutObject",
          "s3:ListBucket",
        ]
        Effect = "Allow"
        Resource = [
          "arn:aws:s3:::${var.s3_bucket_name}",
          "arn:aws:s3:::${var.s3_bucket_name}/*",
        ]
      },
    ]
  })
}

# Attach the policy to the role
resource "aws_iam_role_policy_attachment" "s3_access_attachment" {
  role       = aws_iam_role.ec2_s3_access_role.name
  policy_arn = aws_iam_policy.s3_access_policy.arn
}

# Create an instance profile
resource "aws_iam_instance_profile" "ec2_s3_profile" {
  name = "ec2_s3_profile"
  role = aws_iam_role.ec2_s3_access_role.name
}
*/ 