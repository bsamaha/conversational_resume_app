#!/bin/bash
# Script to download ChromaDB data from S3 at container startup
# Usage: ./download_chroma_from_s3.sh [bucket-name] [environment]

set -e

BUCKET_NAME=${1:-"your-app-data-bucket"}
ENVIRONMENT=${2:-"production"}
DOWNLOAD_DIR="/tmp"
CHROMA_DIR="data/chroma"
ZIP_FILE="${DOWNLOAD_DIR}/chroma_latest.zip"

echo "Checking for ChromaDB data in S3..."

# Check if AWS CLI is installed
if ! command -v aws &> /dev/null; then
    echo "AWS CLI is not installed. Please install it first."
    exit 1
fi

# Create the target directory if it doesn't exist
mkdir -p "$CHROMA_DIR"

# Check if latest ChromaDB data exists in S3
if aws s3 ls "s3://${BUCKET_NAME}/chroma_data/${ENVIRONMENT}/latest.zip" &> /dev/null; then
    echo "Downloading latest ChromaDB data from S3..."
    aws s3 cp "s3://${BUCKET_NAME}/chroma_data/${ENVIRONMENT}/latest.zip" "$ZIP_FILE"
    
    echo "Extracting ChromaDB data..."
    # Remove existing data to avoid conflicts
    rm -rf "${CHROMA_DIR}/*"
    
    # Unzip to the data directory
    unzip -o "$ZIP_FILE" -d "/"
    
    echo "Cleaning up..."
    rm "$ZIP_FILE"
    
    echo "ChromaDB data successfully downloaded and extracted."
else
    echo "No ChromaDB data found in S3. Will need to generate embeddings from raw data."
    
    # Check if raw data exists
    if [ ! -d "data/raw" ] || [ -z "$(ls -A data/raw)" ]; then
        echo "Warning: No raw data found in data/raw. You will need to add resume data and run the ingestion script."
    else
        echo "Raw data found. You can run the ingestion script to generate embeddings."
    fi
fi 