import os
import sys
import logging

# Add the project root directory to Python path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, project_root)

from typing import List, Dict
import numpy as np
import chromadb
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_openai import OpenAIEmbeddings
from dotenv import load_dotenv
from openai import RateLimitError
from pydantic import SecretStr
from chromadb.config import Settings
from backend.app.core.config import get_settings

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO,
                   format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def load_documents(data_dir: str) -> List[Dict[str, str]]:
    """Load documents from the data directory."""
    # Convert the relative data_dir to an absolute path relative to this script
    abs_data_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), data_dir))
    logger.info(f"Loading documents from directory: {abs_data_dir}")
    
    if not os.path.exists(abs_data_dir):
        logger.error(f"Directory does not exist: {abs_data_dir}")
        raise FileNotFoundError(f"Directory not found: {abs_data_dir}")
    
    documents = []
    for filename in os.listdir(abs_data_dir):
        file_path = os.path.join(abs_data_dir, filename)
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

def split_documents(documents: List[Dict[str, str]]) -> List[str]:
    """Split documents into chunks.
    
    For each loaded document, only the 'content' is split using the text splitter.
    """
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=200,
        length_function=len,
    )
    chunks = []
    for doc in documents:
        # Split just the 'content' field from the document dictionary
        chunks.extend(text_splitter.split_text(doc["content"]))
    return chunks

def create_embeddings(chunks: List[str]) -> List[List[float]]:
    """Create embeddings for text chunks."""
    # Get the API key from environment as a normal string, ensuring it's non-null.
    api_key = os.getenv('OPENAI_API_KEY')
    if not api_key:
        raise ValueError("OPENAI_API_KEY is not set in the environment variables.")
    
    embeddings = OpenAIEmbeddings(
        # Wrap the API key with SecretStr
        api_key=SecretStr(api_key),
        model="text-embedding-3-small"
    )
    embedding_list = []
    for chunk in chunks:
        try:
            emb = embeddings.embed_query(chunk)
            embedding_list.append(emb)
        except RateLimitError as e:
            print("RateLimitError encountered:")
            print("You have exceeded your OpenAI API quota. Please check your plan and billing details.")
            raise e
        except Exception as e:
            print(f"Error generating embedding for chunk '{chunk[:30]}...': {e}")
            raise e
    return embedding_list

def store_in_chroma(chunks: List[str], embeddings: List[List[float]]):
    """Store chunks and embeddings in ChromaDB."""
    settings = get_settings()
    persist_dir = settings.chroma_db_path
    logger.info(f"Storing data in ChromaDB at persistence directory: {persist_dir}")
    
    # Ensure the persistence directory exists
    try:
        os.makedirs(persist_dir, exist_ok=True)
        logger.info(f"Created/verified persistence directory: {persist_dir}")
    except Exception as e:
        logger.error(f"Failed to create persistence directory: {str(e)}")
        raise
    
    try:
        client = chromadb.PersistentClient(
            path=persist_dir,
            settings=Settings(anonymized_telemetry=False)
        )
        logger.info("Successfully created ChromaDB client")
        
        collection = client.get_or_create_collection("resume_data")
        logger.info("Successfully created/accessed 'resume_data' collection")
        
        # Use upsert instead of add to avoid adding duplicate documents
        for i, (chunk, embedding) in enumerate(zip(chunks, embeddings)):
            logger.info(f"Upserting chunk {i} (length: {len(chunk)} chars)")
            collection.upsert(
                documents=[chunk],
                embeddings=[embedding],
                ids=[f"chunk_{i}"]
            )
        
        logger.info(f"Successfully stored {len(chunks)} chunks in ChromaDB")
    except Exception as e:
        logger.error(f"Error storing data in ChromaDB: {str(e)}")
        raise

def main():
    # Load documents from the specified directory.
    documents = load_documents("../data/raw")
    
    # Generate text chunks from the loaded documents.
    chunks = split_documents(documents)
    
    # Create embeddings for each text chunk.
    embeddings = create_embeddings(chunks)
    
    # Store the generated embeddings in ChromaDB.
    store_in_chroma(chunks, embeddings)

    print(f"Loaded {len(documents)} documents.")

if __name__ == "__main__":
    main()
