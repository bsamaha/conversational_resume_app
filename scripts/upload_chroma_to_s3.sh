#!/bin/bash
# Script to upload ChromaDB data to S3
# Usage: ./upload_chroma_to_s3.sh [bucket-name] [environment]

set -e

BUCKET_NAME=${1:-"your-app-data-bucket"}
ENVIRONMENT=${2:-"production"}
TIMESTAMP=$(date +%Y%m%d%H%M%S)
CHROMA_DIR="data/chroma"
ZIP_FILE="chroma_data_${ENVIRONMENT}_${TIMESTAMP}.zip"

# Check if AWS CLI is installed
if ! command -v aws &> /dev/null; then
    echo "AWS CLI is not installed. Please install it first."
    exit 1
fi

# Check if the ChromaDB directory exists
if [ ! -d "$CHROMA_DIR" ]; then
    echo "ChromaDB directory not found at $CHROMA_DIR"
    exit 1
fi

echo "Creating zip archive of ChromaDB data..."
zip -r "$ZIP_FILE" "$CHROMA_DIR"

echo "Uploading to S3..."
aws s3 cp "$ZIP_FILE" "s3://${BUCKET_NAME}/chroma_data/${ENVIRONMENT}/${ZIP_FILE}"

# Also upload to a fixed location for latest version
aws s3 cp "$ZIP_FILE" "s3://${BUCKET_NAME}/chroma_data/${ENVIRONMENT}/latest.zip"

echo "Cleaning up..."
rm "$ZIP_FILE"

echo "Done! ChromaDB data uploaded to:"
echo "s3://${BUCKET_NAME}/chroma_data/${ENVIRONMENT}/${ZIP_FILE}"
echo "s3://${BUCKET_NAME}/chroma_data/${ENVIRONMENT}/latest.zip" 