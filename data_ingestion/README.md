# ChromaDB Data Ingestion and S3 Upload

This directory contains the script for processing raw documents, generating embeddings, storing them in ChromaDB, and automatically uploading the data to Amazon S3 for deployment.

## Overview

The ingestion pipeline performs the following steps:
1. Load raw documents from `data/raw/`
2. Split documents into appropriate chunks
3. Generate embeddings for each chunk using OpenAI's embedding model
4. Store the chunks and embeddings in a local ChromaDB instance
5. Create a zip archive of the ChromaDB data with proper path handling
6. Upload the zip to Amazon S3 for use by the deployed application

## Environment Configuration

Set the following environment variables in your `.env` file:

```
# OpenAI API key for generating embeddings
OPENAI_API_KEY=your-openai-api-key

# S3 configuration
S3_DATA_BUCKET=your-app-data-bucket
AWS_ACCESS_KEY_ID=your-aws-access-key
AWS_SECRET_ACCESS_KEY=your-aws-secret-key
AWS_REGION=us-east-2

# Environment settings
ENV=production  # or development

# Embedding model configuration
EMBEDDING_MODEL=text-embedding-3-small
```

## Usage

### Running the Ingestion Pipeline

Run the ingestion process, which will process documents, create embeddings, and upload to S3:

```bash
cd /path/to/project
python -m data_ingestion.ingest
```

S3 upload is automatically enabled when `S3_DATA_BUCKET` is set in your environment variables. No additional flags are required.

## Troubleshooting

### Path Separator Issues

The script addresses a common issue with zip files created on Windows systems, which use backslash (`\`) path separators. When these zip files are extracted on Linux systems (like in Docker containers), they can cause path-related problems.

This implementation ensures that:
1. Files are zipped using Python's `zipfile` module, which handles path separators correctly
2. Path separators are explicitly converted to forward slashes during zip creation
3. The extraction process in the container should work consistently across operating systems

### AWS Credentials

If you're getting S3 upload errors, check that:
1. The AWS credentials in your `.env` file are correct
2. The configured IAM user has permission to write to the S3 bucket
3. The S3 bucket exists in the specified region

### Data Structure

The ChromaDB data should be structured as follows:
```
data/
  chroma/
    chroma.sqlite3
    [collection-uuid]/
      data_level0.bin
      header.bin
      length.bin
      link_lists.bin
```

This structure will be preserved in the zip file under a `chroma/` directory. 