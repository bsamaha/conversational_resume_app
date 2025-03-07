import os
import sys
import logging
import time
import re
import json
import zipfile
import shutil
import tempfile
from datetime import datetime

# Add the project root directory to Python path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, project_root)

from typing import List, Dict, Any
import numpy as np
import chromadb
from langchain.text_splitter import RecursiveCharacterTextSplitter, MarkdownHeaderTextSplitter
from langchain_openai import OpenAIEmbeddings
from dotenv import load_dotenv
from openai import RateLimitError
from pydantic import SecretStr
import openai

# Import AWS SDK for S3 operations
import boto3
from botocore.exceptions import ClientError

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO,
                   format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Get embedding model from environment directly to avoid backend config issues
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "text-embedding-3-small")
logger.info(f"Using embedding model from environment: {EMBEDDING_MODEL}")

# S3 configuration from environment variables
S3_DATA_BUCKET = os.getenv("S3_DATA_BUCKET", "")
ENVIRONMENT = os.getenv("ENV", "production")
# Whether to upload data to S3 after ingestion (default to true if S3_DATA_BUCKET is set)
UPLOAD_TO_S3 = S3_DATA_BUCKET != ""

# Dictionary of supported models and their dimensions
EMBEDDING_DIMENSIONS = {
    "text-embedding-3-small": 1536,
    "text-embedding-3-large": 3072,
    "text-embedding-ada-002": 1536
}

if EMBEDDING_MODEL in EMBEDDING_DIMENSIONS:
    expected_dim = EMBEDDING_DIMENSIONS[EMBEDDING_MODEL]
    logger.info(f"Expected embedding dimensions: {expected_dim}")
else:
    logger.warning(f"Unknown embedding model: {EMBEDDING_MODEL}. Dimension validation will be skipped.")

def load_documents(data_dir: str) -> List[Dict[str, str]]:
    """Load documents from a specified directory."""
    # Ensure data_dir is an absolute path for consistent resolution
    if not os.path.isabs(data_dir):
        data_dir = os.path.join(project_root, data_dir)
    
    logger.info(f"Loading documents from directory: {data_dir}")
    
    # Check if directory exists, create it if it doesn't
    if not os.path.exists(data_dir):
        logger.info(f"Creating data directory: {data_dir}")
        try:
            os.makedirs(data_dir, exist_ok=True)
        except Exception as e:
            logger.error(f"Failed to create directory: {str(e)}")
            raise
    
    documents = []
    for filename in os.listdir(data_dir):
        file_path = os.path.join(data_dir, filename)
        logger.info(f"Processing file: {file_path}")
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            documents.append({"filename": filename, "content": content})
            logger.info(f"Successfully loaded {filename} ({len(content)} characters)")
        except Exception as e:
            logger.error(f"Error loading file {filename}: {str(e)}")
            raise
    return documents

def split_documents(documents: List[Dict[str, str]]) -> List[Dict[str, Any]]:
    """Split documents into chunks while preserving context.
    
    For each document, split the content while maintaining semantic context,
    and preserve metadata including filename and section headers.
    """
    # Create a splitter that respects markdown headers and semantic boundaries
    markdown_splitter = MarkdownHeaderTextSplitter(
        headers_to_split_on=[
            ("#", "header1"),
            ("##", "header2"),
            ("###", "header3"),
        ]
    )

    # Use a more conservative character splitter with increased overlap as fallback
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=2000,  # Increased chunk size to keep more context together
        chunk_overlap=500,  # Larger overlap to maintain continuity between chunks
        length_function=len,
        separators=["\n\n", "\n", ". ", " ", ""]  # Prioritize natural breaks
    )

    all_chunks = []

    for doc in documents:
        filename = doc["filename"]
        content = doc["content"]

        # Special handling for resume files to preserve job entries
        if "resume" in filename.lower():
            try:
                # First split by main sections (## headers)
                md_splits = markdown_splitter.split_text(content)

                for md_section in md_splits:
                    # Extract header information
                    header_info = {
                        key: md_section.metadata.get(key, "") 
                        for key in ["header1", "header2", "header3"] 
                        if key in md_section.metadata
                    }

                    # Special handling for work experience section
                    if header_info.get("header2", "").lower() == "work experience":
                        # Try to split by job entries (### headers) instead of arbitrary chunking
                        job_sections = []

                        # If it has header3, it likely represents individual jobs
                        if "header3" in header_info and header_info["header3"]:
                            # Keep this job entry as a whole chunk
                            job_sections = [md_section.page_content]
                        else:
                            # For work experience without clear job headers,
                            # try to identify job entries by company/date patterns
                            job_pattern = r'(###\s.+?(?=###|\Z)|\*\*([^*|]+?)\*\*[^*]+?(?=\*\*|\Z))'
                            job_matches = re.findall(job_pattern, md_section.page_content, re.DOTALL)

                            job_sections = job_matches or [md_section.page_content]
                        # Create a chunk for each job section
                        for job_content in job_sections:
                            # Enhance header info with job-specific metadata
                            job_title_match = re.search(r'###\s*([^|]+?)(?=\||$)', job_content)
                            job_location_match = re.search(r'\|\s*([^|]+)', job_content)
                            job_dates_match = re.search(r'\|\s*([^|]+?)\s*–\s*([^|]+)', job_content)

                            job_header_info = header_info.copy()
                            if job_title_match:
                                job_header_info["job_title"] = job_title_match[1].strip()
                            if job_location_match:
                                job_header_info["job_location"] = job_location_match[1].strip()
                            if job_dates_match:
                                job_header_info["job_period"] = job_dates_match[0].strip()

                            all_chunks.append({
                                "content": job_content,
                                "filename": filename,
                                "metadata": job_header_info,
                                "section_type": "work_experience"
                            })
                    else:
                        # Standard processing for non-work experience sections
                        section_chunks = text_splitter.split_text(md_section.page_content)

                        all_chunks.extend(
                            {
                                "content": chunk,
                                "filename": filename,
                                "metadata": header_info,
                                "section_type": header_info.get("header2", "")
                                .lower()
                                .replace(" ", "_"),
                            }
                            for chunk in section_chunks
                        )
            except Exception as e:
                logger.warning(f"Error with resume-specific splitting: {e}. Falling back to standard chunking.")
                # Continue with standard chunking below
        else:
            # Standard processing for non-resume documents
            try:
                # First try to split by markdown headers to preserve document structure
                md_splits = markdown_splitter.split_text(content)

                # For each markdown section, further split if needed
                for md_section in md_splits:
                    # Extract header information
                    header_info = {
                        key: md_section.metadata.get(key, "") 
                        for key in ["header1", "header2", "header3"] 
                        if key in md_section.metadata
                    }

                    # Further split large sections while preserving metadata
                    section_chunks = text_splitter.split_text(md_section.page_content)

                    all_chunks.extend(
                        {
                            "content": chunk,
                            "filename": filename,
                            "metadata": header_info,
                            "section_type": header_info.get("header2", "")
                            .lower()
                            .replace(" ", "_"),
                        }
                        for chunk in section_chunks
                    )
            except Exception as e:
                logger.warning(f"Error splitting document by headers: {e}. Falling back to basic chunking.")
                # Fallback to basic chunking if markdown splitting fails
                basic_chunks = text_splitter.split_text(content)
                all_chunks.extend(
                    {
                        "content": chunk,
                        "filename": filename,
                        "metadata": {},
                        "section_type": "general",
                    }
                    for chunk in basic_chunks
                )
    logger.info(f"Split {len(documents)} documents into {len(all_chunks)} chunks")
    return all_chunks

def create_embeddings(chunks: List[Dict[str, Any]]) -> List[List[float]]:
    """Create embeddings for document chunks using OpenAI's embedding model."""
    try:
        logger.info(f"Creating embeddings for {len(chunks)} chunks using {EMBEDDING_MODEL}")
        
        # Initialize OpenAI client with API key from environment
        client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        
        # Prepare enhanced text for each chunk to improve embeddings quality
        texts = [create_enhanced_text(chunk) for chunk in chunks]
        
        # Process in batches for efficiency and to avoid API rate limits
        batch_size = 20  # Adjust based on your API tier and chunk sizes
        embeddings = []
        
        for i in range(0, len(texts), batch_size):
            batch_texts = texts[i:i+batch_size]
            logger.info(f"Processing batch {i//batch_size + 1} with {len(batch_texts)} chunks")
            
            # Create embeddings for the current batch
            response = client.embeddings.create(
                model=EMBEDDING_MODEL,
                input=batch_texts,
                encoding_format="float",
            )
            
            # Extract and store the embeddings for each text in the batch
            batch_embeddings = [item.embedding for item in response.data]
            embeddings.extend(batch_embeddings)
            
            # Add a small delay to avoid hitting rate limits
            if i + batch_size < len(texts):
                time.sleep(0.5)
        
        logger.info(f"Successfully created embeddings for {len(chunks)} chunks")
        
        if embeddings:
            actual_dim = len(embeddings[0])
            logger.info(f"Actual embedding dimension: {actual_dim}")
            
            # Compare with expected dimensions if available
            if EMBEDDING_MODEL in EMBEDDING_DIMENSIONS:
                expected_dim = EMBEDDING_DIMENSIONS[EMBEDDING_MODEL]
                if actual_dim != expected_dim:
                    logger.warning(f"⚠️ DIMENSION MISMATCH: Embeddings have dimension {actual_dim}, "
                                  f"but model {EMBEDDING_MODEL} should produce {expected_dim} dimensions")
        
        return embeddings
    
    except Exception as e:
        logger.error(f"Error creating embeddings: {str(e)}")
        raise

def create_enhanced_text(chunk: Dict[str, Any]) -> str:
    """Create enhanced text representation by incorporating metadata and markdown structure."""
    # Base content
    content = chunk["content"]

    # Extract metadata to provide context
    filename = chunk["filename"]
    metadata = chunk["metadata"]
    section_type = chunk.get("section_type", "")

    # Build enhanced text with a structured format that includes metadata
    enhanced_text_parts = []

    # Special handling for resume work experience sections
    if "resume" in filename.lower() and section_type == "work_experience":
        # Add document identification
        enhanced_text_parts.append("Document: Professional Resume")

        # Extract and format job information from metadata or content
        job_title = metadata.get("job_title", "")
        if not job_title:
            if title_match := re.search(
                r'###\s*([^|]+?)(?=\||$)|^\*\*([^*|]+?)\*\*',
                content,
                re.MULTILINE,
            ):
                job_title = title_match[1] or title_match[2]

        if job_title:
            enhanced_text_parts.append(f"Position: {job_title.strip()}")

        # Extract company
        company = metadata.get("company", "")
        if not company:
            if company_match := re.search(
                r'[-–]\s*([A-Za-z0-9\s&]+)(?=\s*\|)|###.*?[-–]\s*([A-Za-z0-9\s&]+)',
                content,
            ):
                company = company_match[1] or company_match[2]

        if company:
            enhanced_text_parts.append(f"Company: {company.strip()}")

        # Extract location
        location = metadata.get("job_location", "")
        if not location:
            if location_match := re.search(
                r'\|\s*([^|]+?)(?=\s*\||$)', content
            ):
                location = location_match[1]

        if location:
            enhanced_text_parts.append(f"Location: {location.strip()}")

        # Extract employment period
        period = metadata.get("job_period", "")
        if not period:
            if period_match := re.search(
                r'\|\s*([^|]+?)\s*–\s*([^|]+?)(?=\s*\||$)', content
            ):
                period = f"{period_match[1].strip()} – {period_match[2].strip()}"

        if period:
            enhanced_text_parts.append(f"Period: {period}")

        # Extract specific dates as backup
        date_pattern = r'\b(January|February|March|April|May|June|July|August|September|October|November|December|Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]* \d{4}\b'
        dates = re.findall(date_pattern, content)
        if dates and not period:
            enhanced_text_parts.append(f"Dates mentioned: {', '.join(dates)}")

        # Add explicit first job marker if this appears to be the first job
        if any(company in ["Entergy", "United States Marine Corps", "Marine Corps", "USMC"] for company in [company, content]):
            enhanced_text_parts.extend(("FIRST JOB: Yes", "CAREER START: Yes"))
        enhanced_text_parts.extend(
            ("Section: Work Experience", "Category: Employment History")
        )
    else:
        # Extract document type from filename (e.g., "resume", "job_overview", etc.)
        doc_type = filename.split('.')[0].replace('_', ' ').title()
        enhanced_text_parts.extend(
            (f"Document Type: {doc_type}", f"Source: {filename}")
        )
        # Add header context if available
        headers = []
        if "header1" in metadata and metadata["header1"]:
            headers.append(f"Section: {metadata['header1']}")
        if "header2" in metadata and metadata["header2"]:
            headers.append(f"Subsection: {metadata['header2']}")
        if "header3" in metadata and metadata["header3"]:
            headers.append(f"Topic: {metadata['header3']}")

        if headers:
            enhanced_text_parts.append(" > ".join(headers))

        if section_type:
            enhanced_text_parts.append(f"Section Type: {section_type}")

    if entities := extract_markdown_entities(content):
        # Group entities by type for better organization
        entity_types = {}
        for entity in entities:
            if ":" in entity:
                entity_type, value = entity.split(":", 1)
                if entity_type not in entity_types:
                    entity_types[entity_type] = []
                entity_types[entity_type].append(value)

        # Add grouped entities to enhanced text
        enhanced_text_parts.extend(f"{entity_type.title()}: {', '.join(values)}" 
                                for entity_type, values in entity_types.items())

    # Add the main content
    enhanced_text_parts.append(f"Content: {content}")

    return "\n".join(enhanced_text_parts)

def extract_markdown_entities(content: str) -> List[str]:
    """Extract key entities from markdown content based on patterns, with special handling for resumes."""
    entities = []

    # Extract dates with month-year format (common in resumes and work experience)
    date_pattern = r'\b(January|February|March|April|May|June|July|August|September|October|November|December|Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]* \d{4}\b'
    dates = re.findall(date_pattern, content)
    if dates:
        entities.extend([f"date:{date}" for date in set(dates)])

    # Extract year ranges (common in work experience entries)
    year_range_pattern = r'\b(20\d{2})\s*(?:–|-|to)\s*(20\d{2}|Present)\b'
    if year_ranges := re.findall(year_range_pattern, content, re.IGNORECASE):
        entities.extend([f"period:{start}-{end}" for start, end in year_ranges])

    # Extract job titles (often in bold or headers in resumes)
    job_title_patterns = [
        r'###\s*([^|]+?)(?=\||$)',                   # Job titles in headers
        r'\*\*([^*|]+?)\*\*(?=\s*\|)',               # Bold job titles before pipe
        r'(Senior|Lead|Principal|Chief|Head|Director|Manager|Engineer|Architect|Developer)\s+[A-Za-z\s]+',  # Common job title patterns
    ]

    for pattern in job_title_patterns:
        if job_titles := re.findall(pattern, content):
            # Flatten list if there are groups
            if isinstance(job_titles[0], tuple):
                job_titles = [item for sublist in job_titles for item in sublist if item]

            # Clean and add job titles
            for title in set(job_titles):
                clean_title = title.strip()
                if clean_title and len(clean_title) < 50:  # Sanity check
                    entities.append(f"job_title:{clean_title}")

    # Extract company names (typically following job titles, after pipe or dash)
    company_patterns = [
        r'[-–]\s*([A-Za-z0-9\s&]+)(?=\s*\|)',                # Company after dash before pipe
        r'\|\s*([^|]+?)\s*\|\s*([^|]+?)\s*–',                # Company between pipes before date range
        r'(at|for|with)\s+([A-Z][A-Za-z0-9\s&]+)(?:\s*\(|\s|$)',  # "at Company" pattern
        r'([A-Z][A-Za-z0-9\s&]+?)\s*\|\s*[A-Za-z]+,\s*[A-Z]{2}',  # Company before location
    ]

    for pattern in company_patterns:
        if companies := re.findall(pattern, content):
            # Flatten list if there are groups
            if isinstance(companies[0], tuple):
                companies = [item for sublist in companies for item in sublist if item]

            # Clean and filter common false positives
            for company in set(companies):
                clean_company = company.strip()
                # Skip common false positives and prepositions
                if clean_company.lower() in ['at', 'for', 'with', 'the', 'and', 'llc']:
                    continue
                if clean_company and len(clean_company) < 50:  # Sanity check
                    entities.append(f"company:{clean_company}")

    # Explicitly check for your specific companies
    company_names = [
        "Occidental Petroleum", "Oxy", 
        "u-blox", 
        "Clutch Sports Data",
        "Enchanted Rock", 
        "Entergy", 
        "United States Marine Corps", "Marine Corps", "USMC"
    ]

    entities.extend(f"company:{company}" for company in company_names 
                  if re.search(r'\b' + re.escape(company) + r'\b', content, re.IGNORECASE))

    # Extract locations (cities, states)
    location_patterns = [
        r'([A-Z][a-z]+,\s*[A-Z]{2})',                   # City, State format
        r'\|\s*([A-Z][a-z]+(?:,\s*[A-Z]{2})?)\s*\|',    # Location between pipes
    ]

    for pattern in location_patterns:
        if locations := re.findall(pattern, content):
            # Add unique locations
            entities.extend(f"location:{location.strip()}" for location in set(locations) if location.strip())

    # Extract skills and technologies (often in bullet points or skills section)
    skill_sets = {
        "languages": ["Java", "Python", "C#", "JavaScript", "C\\+\\+", "TypeScript", "Go", "Ruby"],
        "cloud": ["AWS", "Azure", "GCP", "Google Cloud", "Cloud Platform"],
        "databases": ["SQL", "MySQL", "PostgreSQL", "MongoDB", "DynamoDB", "Cosmos DB", "SQL Server"],
        "technologies": ["Docker", "Kubernetes", "Terraform", "Ansible", "Jenkins", "Git", "GitHub", "MQTT", "Kafka", "IoT"]
    }

    for category, skills in skill_sets.items():
        entities.extend(f"{category}:{skill}" for skill in skills if re.search(r'\b' + re.escape(skill) + r'\b', content))

    return entities

def store_in_chroma(chunks: List[Dict[str, Any]], embeddings: List[List[float]]):
    """Store chunks and embeddings in ChromaDB with enhanced metadata for markdown documents."""
    # Use project root data directory for consistency across the application
    default_persist_dir = os.path.join(project_root, "data/chroma")
    persist_dir = os.getenv("CHROMA_DB_PATH", default_persist_dir)
    logger.info(f"Storing data in ChromaDB at persistence directory: {persist_dir}")

    # Ensure the persistence directory exists
    try:
        os.makedirs(persist_dir, exist_ok=True)
        logger.info(f"Created/verified persistence directory: {persist_dir}")
    except Exception as e:
        logger.error(f"Failed to create persistence directory: {str(e)}")
        raise

    try:
        # Initialize ChromaDB client
        client = chromadb.PersistentClient(
            path=persist_dir
        )
        logger.info("Successfully created ChromaDB client")

        # Always delete the existing collection to ensure a complete refresh
        try:
            logger.info("Attempting to delete existing 'resume_data' collection if it exists")
            client.delete_collection("resume_data")
            logger.info("Successfully deleted existing collection")
        except Exception as e:
            logger.info(f"No existing collection to delete or error: {str(e)}")

        # Create a fresh collection
        collection = client.create_collection(
            name="resume_data",
            metadata={"hnsw:space": "cosine"}  # Use cosine similarity for better semantic matching
        )
        logger.info("Successfully created fresh 'resume_data' collection")

        # Add chunks with their embeddings to the collection
        for i, chunk in enumerate(chunks):
            # Get the chunk content and enhanced metadata
            content = chunk["content"]
            filename = chunk.get("filename", "unknown")
            section_type = chunk.get("section_type", "")

            # Extract metadata from the chunk
            metadata = {
                "source": filename,
                "section_type": section_type,
            }

            # Add header info to metadata
            chunk_metadata = chunk.get("metadata", {})
            for key, value in chunk_metadata.items():
                if value:  # Only add non-empty values
                    metadata[key] = value

            # Special handling for job-related entries
            if "resume" in filename.lower() and section_type == "work_experience":
                # Try to extract job-specific info not already in metadata
                if "job_title" not in metadata:
                    if title_match := re.search(
                        r'###\s*([^|]+?)(?=\||$)|^\*\*([^*|]+?)\*\*',
                        content,
                        re.MULTILINE,
                    ):
                        job_title = title_match[1] or title_match[2]
                        metadata["job_title"] = job_title.strip()

                # Extract company if not in metadata
                if "company" not in metadata:
                    if company_match := re.search(
                        r'[-–]\s*([A-Za-z0-9\s&]+)(?=\s*\|)|###.*?[-–]\s*([A-Za-z0-9\s&]+)',
                        content,
                    ):
                        company = company_match[1] or company_match[2]
                        metadata["company"] = company.strip()

                # Also check for specific companies by name
                company_names = [
                    "Occidental Petroleum", "Oxy", 
                    "u-blox", 
                    "Clutch Sports Data",
                    "Enchanted Rock", 
                    "Entergy", 
                    "United States Marine Corps", "Marine Corps", "USMC"
                ]

                for company in company_names:
                    if re.search(r'\b' + re.escape(company) + r'\b', content, re.IGNORECASE):
                        metadata["company"] = company
                        # First job companies
                        if company.lower() in ["entergy", "united states marine corps", "marine corps", "usmc"]:
                            metadata["first_job"] = "true"

                if date_range_match := re.search(
                    r'\|\s*([^|]+?)\s*–\s*([^|]+?)(?=\s*\||$)', content
                ):
                    metadata["start_date"] = date_range_match[1].strip()
                    metadata["end_date"] = date_range_match[2].strip()
                    metadata["date_range"] = (
                        f"{date_range_match[1].strip()} – {date_range_match[2].strip()}"
                    )

            # Generate a consistent ID for the chunk
            chunk_id = f"chunk_{i:04d}"

            # Create document description for logging clarity
            doc_description = f"{filename}"
            if "company" in metadata:
                doc_description += f" - {metadata['company']}"
            if "job_title" in metadata:
                doc_description += f" ({metadata['job_title']})"

            # Log progress with useful details
            logger.info(f"Upserting chunk {i}: {doc_description} (length: {len(content)} chars)")

            # Add to ChromaDB
            collection.add(
                documents=[content],
                embeddings=[embeddings[i]],
                metadatas=[metadata],
                ids=[chunk_id]
            )

        logger.info(f"Successfully stored {len(chunks)} chunks in ChromaDB")

    except Exception as e:
        logger.error(f"Failed to store data in ChromaDB: {str(e)}", exc_info=True)
        raise

def save_to_s3(chroma_dir: str) -> bool:
    """
    Zip and upload ChromaDB data to S3.
    
    Args:
        chroma_dir: Path to the ChromaDB directory
        
    Returns:
        True if successful, False otherwise
    """
    if not S3_DATA_BUCKET:
        logger.warning("S3_DATA_BUCKET not set. Skipping S3 upload.")
        return False
        
    logger.info(f"Preparing to upload ChromaDB data to S3 bucket {S3_DATA_BUCKET}...")
    
    try:
        # Ensure chroma_dir is absolute
        if not os.path.isabs(chroma_dir):
            chroma_dir = os.path.join(project_root, chroma_dir)
            
        # Create timestamp for unique zip filename
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        
        # Create temporary directory structure for zip creation
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create a temporary zip file
            zip_path = os.path.join(tmpdir, f"chroma_data_{timestamp}.zip")
            tmp_chroma_dir = os.path.join(tmpdir, "chroma")
            
            # Copy ChromaDB files to temp directory
            logger.info("Copying ChromaDB data to temporary directory...")
            shutil.copytree(chroma_dir, tmp_chroma_dir)
            
            # Create a platform-independent zip file
            logger.info(f"Creating zip archive...")
            with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                for root, _, files in os.walk(tmp_chroma_dir):
                    for file in files:
                        file_path = os.path.join(root, file)
                        # Use forward slashes for paths in zip (works on all platforms)
                        arcname = os.path.join("chroma", os.path.relpath(file_path, tmp_chroma_dir)).replace('\\', '/')
                        zipf.write(file_path, arcname)
            
            # Create S3 client
            s3_client = boto3.client('s3')
            
            # Upload to S3 with timestamp
            timestamped_key = f"chroma_data/{ENVIRONMENT}/chroma_data_{timestamp}.zip"
            logger.info(f"Uploading to s3://{S3_DATA_BUCKET}/{timestamped_key}...")
            s3_client.upload_file(zip_path, S3_DATA_BUCKET, timestamped_key)
            
            # Also upload as "latest" for the container to use
            latest_key = f"chroma_data/{ENVIRONMENT}/latest.zip"
            logger.info(f"Setting as latest version at s3://{S3_DATA_BUCKET}/{latest_key}...")
            s3_client.copy_object(
                Bucket=S3_DATA_BUCKET,
                CopySource={'Bucket': S3_DATA_BUCKET, 'Key': timestamped_key},
                Key=latest_key
            )
            
            logger.info("✅ Successfully uploaded ChromaDB data to S3")
            return True
            
    except Exception as e:
        logger.error(f"Failed to upload ChromaDB data to S3: {str(e)}", exc_info=True)
        return False

def main():
    """
    Main function to process documents and store them in ChromaDB.
    This will COMPLETELY REPLACE any existing data in the collection.
    """
    logger.warning(
        "⚠️  WARNING: This script will COMPLETELY REPLACE all existing data in ChromaDB. "
        "All previous embeddings will be lost.")

    # Short pause to allow user to see the warning
    time.sleep(2)

    # Log which embedding model we're using
    logger.info(f"Using embedding model: {EMBEDDING_MODEL}")
    if EMBEDDING_MODEL in EMBEDDING_DIMENSIONS:
        logger.info(f"Expected embedding dimension: {EMBEDDING_DIMENSIONS[EMBEDDING_MODEL]}")

    # Load documents from the specified directory.
    # Use path relative to the project root for consistency
    documents = load_documents("data/raw")
    logger.info(f"Loaded {len(documents)} documents from data/raw")

    # Generate text chunks from the loaded documents
    logger.info("Splitting documents into chunks...")
    chunks = split_documents(documents)
    logger.info(f"Generated {len(chunks)} chunks from {len(documents)} documents")

    # Get embeddings for each chunk
    logger.info(f"Creating embeddings for {len(chunks)} chunks...")
    embeddings = create_embeddings(chunks)
    logger.info(f"Successfully created {len(embeddings)} embeddings")

    # Store the chunks and embeddings in ChromaDB
    logger.info("Storing data in ChromaDB...")
    store_in_chroma(chunks, embeddings)

    logger.info("✅ Document ingestion complete. All data has been replaced with new embeddings.")

    # Upload ChromaDB data to S3 if bucket is configured
    chroma_dir = os.path.join(project_root, "data/chroma")
    if UPLOAD_TO_S3:
        logger.info("Starting S3 upload of ChromaDB data...")
        if upload_success := save_to_s3(chroma_dir):
            logger.info("✅ S3 upload completed successfully")
        else:
            logger.warning("⚠️ S3 upload failed, but local ChromaDB data is still valid")
    else:
        logger.info("S3 upload skipped (S3_DATA_BUCKET not configured)")

    logger.info(f"Data is now available for the conversational resume using model: {EMBEDDING_MODEL}")
    
if __name__ == "__main__":
    main()
