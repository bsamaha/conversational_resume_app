import os
import logging
import boto3
import zipfile
import tempfile
import shutil
from typing import Optional
from botocore.exceptions import ClientError
from app.core.config import settings

# Configure logging
logger = logging.getLogger(__name__)

def check_aws_credentials() -> bool:
    """
    Check if AWS credentials are available from any source.
    Returns True if credentials are available, False otherwise.
    """
    # Create a boto3 client to test credentials
    try:
        sts = boto3.client('sts')
        sts.get_caller_identity()
        logger.info("AWS credentials verified successfully")
        return True
    except Exception as e:
        logger.warning(f"AWS credential check failed: {str(e)}")
        return False

def verify_s3_access(bucket_name: str) -> bool:
    """
    Verify access to an S3 bucket.
    """
    try:
        s3 = boto3.client('s3')
        s3.head_bucket(Bucket=bucket_name)
        logger.info(f"S3 access to bucket '{bucket_name}' confirmed")
        return True
    except ClientError as e:
        error_code = e.response.get('Error', {}).get('Code', 'Unknown')
        if error_code == '404':
            logger.error(f"S3 bucket '{bucket_name}' does not exist")
        elif error_code == '403':
            logger.error(f"Access denied to S3 bucket '{bucket_name}'")
        else:
            logger.error(f"Error accessing S3 bucket '{bucket_name}': {str(e)}")
        return False
    except Exception as e:
        logger.error(f"Unexpected error accessing S3 bucket '{bucket_name}': {str(e)}")
        return False

def download_latest_chroma_data(bucket_name: str, environment: str) -> Optional[str]:
    """
    Download the latest ChromaDB data from S3.
    Returns the path to the downloaded file, or None if the download failed.
    """
    s3 = boto3.client('s3')
    latest_key = f"chroma_data/{environment}/latest.zip"

    try:
        # First try to get the latest.zip file
        if _check_s3_object_exists(s3, bucket_name, latest_key):
            logger.info(f"Found latest.zip at s3://{bucket_name}/{latest_key}")
            download_path = tempfile.mktemp(suffix='.zip')
            s3.download_file(bucket_name, latest_key, download_path)
        else:
            # If latest.zip doesn't exist, find the most recent timestamped file
            logger.info("No latest.zip found. Looking for timestamped files...")
            prefix = f"chroma_data/{environment}/"
            response = s3.list_objects_v2(Bucket=bucket_name, Prefix=prefix)

            if 'Contents' not in response or len(response['Contents']) == 0:
                logger.warning(f"No ChromaDB data files found in s3://{bucket_name}/{prefix}")
                return None

            # Filter for .zip files and sort by last modified date
            zip_files = [obj for obj in response['Contents'] 
                        if obj['Key'].endswith('.zip') and obj['Key'] != latest_key]

            if not zip_files:
                logger.warning(f"No ChromaDB data ZIP files found in s3://{bucket_name}/{prefix}")
                return None

            # Sort by last modified (newest first)
            zip_files.sort(key=lambda x: x['LastModified'], reverse=True)
            latest_file = zip_files[0]['Key']

            logger.info(f"Found latest timestamped file: {latest_file}")
            download_path = tempfile.mktemp(suffix='.zip')
            s3.download_file(bucket_name, latest_file, download_path)
        logger.info(f"Downloaded latest ChromaDB data to {download_path}")
        return download_path
    except Exception as e:
        logger.error(f"Error downloading ChromaDB data: {str(e)}")
        return None

def _check_s3_object_exists(s3_client, bucket, key) -> bool:
    """Check if an object exists in S3."""
    try:
        s3_client.head_object(Bucket=bucket, Key=key)
        return True
    except ClientError as e:
        return False

def extract_chroma_data(zip_path: str, chroma_dir: str) -> bool:
    """
    Extract ChromaDB data from a zip file to the target directory.
    Returns True if successful, False otherwise.
    """
    if not zip_path or not os.path.exists(zip_path):
        logger.error(f"Zip file not found: {zip_path}")
        return False
        
    try:
        # Create a temporary directory for extraction
        with tempfile.TemporaryDirectory() as tmpdir:
            logger.info(f"Extracting {zip_path} to temporary directory...")
            
            # Extract the zip file to the temporary directory
            with zipfile.ZipFile(zip_path, 'r') as zipf:
                zipf.extractall(tmpdir)
            
            # Clear the target directory to avoid conflicts
            if os.path.exists(chroma_dir):
                logger.info(f"Clearing existing ChromaDB directory: {chroma_dir}")
                for item in os.listdir(chroma_dir):
                    item_path = os.path.join(chroma_dir, item)
                    if os.path.isfile(item_path):
                        os.unlink(item_path)
                    elif os.path.isdir(item_path):
                        shutil.rmtree(item_path)
            else:
                os.makedirs(chroma_dir, exist_ok=True)
            
            # Find the source directory (either chroma/ or the root)
            src_dir = os.path.join(tmpdir, "chroma")
            if not os.path.exists(src_dir):
                # If no "chroma" directory, use the tempdir itself
                src_dir = tmpdir
            
            # Copy extracted files to the target directory
            for item in os.listdir(src_dir):
                src_item = os.path.join(src_dir, item)
                dst_item = os.path.join(chroma_dir, item)
                if os.path.isfile(src_item):
                    shutil.copy2(src_item, dst_item)
                elif os.path.isdir(src_item):
                    shutil.copytree(src_item, dst_item)
            
            logger.info(f"Successfully extracted ChromaDB data to {chroma_dir}")
            return True
            
    except Exception as e:
        logger.error(f"Error extracting ChromaDB data: {str(e)}")
        return False
    finally:
        # Clean up the downloaded zip file
        try:
            if os.path.exists(zip_path):
                os.unlink(zip_path)
        except Exception as e:
            logger.warning(f"Error cleaning up temporary zip file: {str(e)}")

def initialize_chroma_data() -> bool:
    """
    Main function to initialize ChromaDB data from S3.
    Returns True if successful or if S3 data loading is disabled, False otherwise.
    """
    # Get configuration
    s3_bucket = settings.AWS_S3_BUCKET_NAME or os.getenv("S3_DATA_BUCKET", "conversational-resume")
    environment = settings.ENV
    chroma_dir = settings.CHROMA_DB_PATH
    use_s3_data = os.getenv("USE_S3_DATA", "true").lower() == "true"
    
    # Create necessary directories
    os.makedirs(chroma_dir, exist_ok=True)
    
    # Skip if S3 data loading is disabled
    if not use_s3_data:
        logger.info("S3 data loading is disabled (USE_S3_DATA=false)")
        return True
    
    logger.info(f"Initializing ChromaDB data from S3 bucket {s3_bucket}")
    
    # Check AWS credentials
    if not check_aws_credentials():
        logger.error("AWS credentials not available, cannot download ChromaDB data")
        return False
    
    # Verify S3 access
    if not verify_s3_access(s3_bucket):
        logger.error(f"Cannot access S3 bucket {s3_bucket}")
        return False
    
    # Download the latest ChromaDB data
    zip_path = download_latest_chroma_data(s3_bucket, environment)
    if not zip_path:
        logger.warning("No ChromaDB data found in S3 or download failed")
        return False
    
    # Extract the ChromaDB data
    return extract_chroma_data(zip_path, chroma_dir) 