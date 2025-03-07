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
        
        # Unzip to the data directory
        unzip -o /tmp/chroma_latest.zip -d /
        
        echo "Cleaning up..."
        rm /tmp/chroma_latest.zip
        
        echo "ChromaDB data successfully downloaded and extracted."
    else
        echo "No ChromaDB data found in S3."
    fi
fi

# Check if we have raw data but no ChromaDB data, and process if needed
if [ -d "$RAW_DATA_DIR" ] && [ "$(ls -A $RAW_DATA_DIR)" ] && [ ! "$(ls -A $CHROMA_DIR)" ]; then
    echo "Raw data found but no ChromaDB data. Running ingestion script..."
    
    # Install ingestion requirements if we're in a new environment
    if [ ! -f "${APP_DIR}/.ingestion_installed" ]; then
        echo "Installing ingestion dependencies..."
        pip install -r "${APP_DIR}/data_ingestion/requirements.txt"
        touch "${APP_DIR}/.ingestion_installed"
    fi
    
    # Run the ingestion script
    echo "Processing raw data..."
    cd "${APP_DIR}"
    python "${APP_DIR}/data_ingestion/ingest.py"
    
    # Upload the newly generated ChromaDB data to S3 if configured
    if [ "$USE_S3_DATA" = "true" ] && [ "$AUTO_UPLOAD_DATA" = "true" ] && [ -n "$AWS_ACCESS_KEY_ID" ] && [ -n "$AWS_SECRET_ACCESS_KEY" ]; then
        echo "Uploading newly generated ChromaDB data to S3..."
        TIMESTAMP=$(date +%Y%m%d%H%M%S)
        ZIP_FILE="/tmp/chroma_data_${ENVIRONMENT}_${TIMESTAMP}.zip"
        
        cd "${APP_DIR}"
        zip -r "$ZIP_FILE" "data/chroma"
        
        aws s3 cp "$ZIP_FILE" "s3://${S3_DATA_BUCKET}/chroma_data/${ENVIRONMENT}/chroma_data_${ENVIRONMENT}_${TIMESTAMP}.zip"
        aws s3 cp "$ZIP_FILE" "s3://${S3_DATA_BUCKET}/chroma_data/${ENVIRONMENT}/latest.zip"
        
        rm "$ZIP_FILE"
        echo "ChromaDB data uploaded to S3."
    fi
fi

# Start the application
echo "Starting the application..."
cd "${APP_DIR}"
exec uvicorn app.main:app --host 0.0.0.0 --port 8000 