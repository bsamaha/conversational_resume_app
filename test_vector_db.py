import os
import sys
import logging
import chromadb
from chromadb.config import Settings
import numpy as np
import openai

# Add the project root directory to Python path for consistent imports
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

# Set up logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

# Define constants
EMBEDDING_MODEL = "text-embedding-3-large"  # OpenAI's embedding model to use
# Use absolute path for consistent resolution
CHROMA_DIR = os.path.join(project_root, "data/chroma")  # Path to ChromaDB directory

def get_embedding(text: str) -> list:
    """Get embedding for a text using OpenAI's API."""
    try:
        # Initialize OpenAI client with API key from environment
        client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        
        # Create embedding for the text
        response = client.embeddings.create(
            model=EMBEDDING_MODEL,
            input=text,
            encoding_format="float",
        )
        
        # Extract and return the embedding
        return response.data[0].embedding
    except Exception as e:
        logger.error(f"Error creating embedding: {str(e)}")
        raise

def query_chroma(query_text: str, k: int = 3):
    """Query ChromaDB with the given text and return top k results."""
    try:
        # Get embedding for the query
        logger.info(f"Getting embedding for query: {query_text}")
        query_embedding = get_embedding(query_text)
        
        # Initialize ChromaDB client
        logger.info(f"Connecting to ChromaDB at {CHROMA_DIR}")
        client = chromadb.PersistentClient(
            path=CHROMA_DIR,
            settings=Settings(anonymized_telemetry=False)
        )
        
        # Get the collection
        collection = client.get_collection("resume_data")
        logger.info(f"Successfully connected to ChromaDB collection 'resume_data'")
        
        # Query the collection
        logger.info(f"Querying collection with k={k}")
        results = collection.query(
            query_embeddings=[query_embedding],
            n_results=k,
            include=["documents", "distances", "metadatas"]  # type: ignore
        )
        
        # Extract results
        documents = results.get("documents", [[]])
        distances = results.get("distances", [[]])
        metadatas = results.get("metadatas", [[]])
        
        # Check if we have valid results
        if not documents or len(documents) == 0 or len(documents[0]) == 0:
            logger.warning("No relevant context found in vector store")
            return "No relevant context found."
        
        # Process and print results
        print("\n" + "="*80)
        print(f"QUERY: {query_text}")
        print("="*80)
        
        # Extract the first set of results (from the first query embedding)
        docs = documents[0]
        dists = distances[0] if distances and len(distances) > 0 else []
        metas = metadatas[0] if metadatas and len(metadatas) > 0 else []
        
        for i in range(len(docs)):
            similarity = 1 - dists[i] if i < len(dists) else 0
            print(f"\n--- Result {i+1} (Similarity: {similarity:.4f}) ---")
            
            # Print metadata if available
            if i < len(metas) and metas[i]:
                print("METADATA:")
                for key, value in metas[i].items():
                    print(f"  {key}: {value}")
            
            # Print document content
            print("\nCONTENT:")
            print(docs[i])
            print("-"*80)
        
        return results
    
    except Exception as e:
        logger.error(f"Error querying ChromaDB: {str(e)}")
        raise

def main():
    """Run sample queries to test the vector database."""
    # Sample questions to test
    test_queries = [
        "What are Blake's technical skills?",
        "Tell me about Blake's work experience",
        "Describe a time when Blake faced a difficult situation",
        "What are Blake's salary expectations?",
        "What makes Blake unique as a solution architect?",
        "What is Blake's educational background?"
    ]
    
    # Run each query
    for query in test_queries:
        try:
            query_chroma(query)
        except Exception as e:
            logger.error(f"Error processing query '{query}': {str(e)}")
    
    print("\nTest completed.")

if __name__ == "__main__":
    main() 