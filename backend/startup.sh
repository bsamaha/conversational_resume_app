#!/bin/bash
# Container startup script

set -e

# Default environment variables
S3_DATA_BUCKET=${S3_DATA_BUCKET:-"your-app-data-bucket"}
ENVIRONMENT=${ENV:-"production"}
APP_DIR="/app"
SCRIPTS_DIR="${APP_DIR}/scripts"
DATA_DIR="${APP_DIR}/data"
RAW_DATA_DIR="${DATA_DIR}/raw"
CHROMA_DIR="${DATA_DIR}/chroma"

echo "Starting container in $ENVIRONMENT environment"

# Create data directories if they don't exist
mkdir -p "$RAW_DATA_DIR"
mkdir -p "$CHROMA_DIR"

# Try to download ChromaDB data from S3
if [ "$USE_S3_DATA" = "true" ] && [ -n "$AWS_ACCESS_KEY_ID" ] && [ -n "$AWS_SECRET_ACCESS_KEY" ]; then
    echo "Attempting to download ChromaDB data from S3..."
    
    # Download ChromaDB data from S3
    if aws s3 ls "s3://${S3_DATA_BUCKET}/chroma_data/${ENVIRONMENT}/latest.zip" &> /dev/null; then
        echo "Found ChromaDB data in S3. Downloading..."
        aws s3 cp "s3://${S3_DATA_BUCKET}/chroma_data/${ENVIRONMENT}/latest.zip" /tmp/chroma_latest.zip
        
        echo "Extracting ChromaDB data..."
        # Remove existing data to avoid conflicts
        rm -rf "${CHROMA_DIR:?}/"*
        
        # Create a temporary directory for extraction
        mkdir -p /tmp/chroma_extract
        
        # Unzip to the temporary directory first
        unzip -o /tmp/chroma_latest.zip -d /tmp/chroma_extract
        
        # Move the contents to the correct location
        if [ -d "/tmp/chroma_extract/chroma" ]; then
            # Copy contents of the chroma directory, not the directory itself
            cp -R /tmp/chroma_extract/chroma/* "${CHROMA_DIR}/"
        else
            # If the zip doesn't have a nested chroma folder, copy everything
            cp -R /tmp/chroma_extract/* "${CHROMA_DIR}/"
        fi
        
        echo "Cleaning up..."
        rm /tmp/chroma_latest.zip
        rm -rf /tmp/chroma_extract
        
        echo "ChromaDB data successfully downloaded and extracted to ${CHROMA_DIR}"
    else
        echo "No ChromaDB data found in S3."
    fi
fi

# In production environments, we rely on pre-built ChromaDB data
# We won't try to process raw data as data_ingestion may not be available
if [ "$ENVIRONMENT" = "development" ] && [ -d "$RAW_DATA_DIR" ] && [ "$(ls -A $RAW_DATA_DIR)" ] && [ ! "$(ls -A $CHROMA_DIR)" ]; then
    echo "Development environment detected with raw data but no ChromaDB data."
    echo "Please run the data ingestion process locally before deploying."
    # We don't run ingest.py in production containers
fi

# Start the application
echo "Starting the application..."
cd "${APP_DIR}"
exec uvicorn app.main:app --host 0.0.0.0 --port 8000 