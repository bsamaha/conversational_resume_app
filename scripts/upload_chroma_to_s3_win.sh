#!/bin/bash
# Script to upload ChromaDB data to S3 using 7-Zip for Windows
# Usage: ./upload_chroma_to_s3_win.sh [bucket-name] [environment]

set -e

BUCKET_NAME=${1:-"your-app-data-bucket"}
ENVIRONMENT=${2:-"production"}
TIMESTAMP=$(date +%Y%m%d%H%M%S)
CHROMA_DIR="data/chroma"
ZIP_FILE="chroma_data_${ENVIRONMENT}_${TIMESTAMP}.zip"

# Path to 7-Zip - adjust this if your 7-Zip is installed elsewhere
SEVEN_ZIP_PATH="/c/Program Files/7-Zip/7z.exe"

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

# Check if 7-Zip exists
if [ ! -f "$SEVEN_ZIP_PATH" ]; then
    echo "7-Zip not found at $SEVEN_ZIP_PATH. Please install 7-Zip or adjust the path in the script."
    exit 1
fi

echo "Creating zip archive of ChromaDB data..."
# Use 7-Zip to create the archive
"$SEVEN_ZIP_PATH" a -tzip "$ZIP_FILE" "$CHROMA_DIR"

echo "Uploading to S3..."
aws s3 cp "$ZIP_FILE" "s3://${BUCKET_NAME}/chroma_data/${ENVIRONMENT}/${ZIP_FILE}"

# Also upload to a fixed location for latest version
aws s3 cp "$ZIP_FILE" "s3://${BUCKET_NAME}/chroma_data/${ENVIRONMENT}/latest.zip"

echo "Cleaning up..."
rm "$ZIP_FILE"

echo "Done! ChromaDB data uploaded to:"
echo "s3://${BUCKET_NAME}/chroma_data/${ENVIRONMENT}/${ZIP_FILE}"
echo "s3://${BUCKET_NAME}/chroma_data/${ENVIRONMENT}/latest.zip" 