import logging
from langchain_chroma import Chroma
from chromadb.config import Settings as ChromaSettings
from app.core.config import get_settings
from app.core.embeddings import get_embeddings
from fastapi import HTTPException
import chromadb
import os

# Configure logging
logging.basicConfig(level=logging.INFO,
                   format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

settings = get_settings()

def get_chroma_client():
    try:
        persist_dir = settings.chroma_db_path
        logger.info(f"Initializing Chroma client with persist_directory: {persist_dir}")
        
        # Verify the persistence directory exists
        if not os.path.exists(persist_dir):
            logger.error(f"ChromaDB persistence directory does not exist: {persist_dir}")
            raise FileNotFoundError(f"ChromaDB directory not found: {persist_dir}")
            
        chroma_client = chromadb.PersistentClient(
            path=persist_dir,
            settings=ChromaSettings(anonymized_telemetry=False)
        )
        
        # Verify we can access the collection
        try:
            collection = chroma_client.get_collection("resume_data")
            count = collection.count()
            logger.info(f"Successfully connected to ChromaDB. Collection 'resume_data' contains {count} documents.")
        except Exception as e:
            logger.error(f"Collection 'resume_data' not found or empty: {str(e)}")
            raise
            
        return chroma_client
    except Exception as e:
        logger.error("Error initializing Chroma client", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to initialize ChromaDB: {str(e)}")

async def get_relevant_context(query: str, k: int = 3) -> str:
    try:
        logger.info(f"Retrieving context for query: {query}")
        client = get_chroma_client()
        
        try:
            collection = client.get_collection("resume_data")
            logger.info("Successfully retrieved collection 'resume_data'")
        except Exception as e:
            logger.error(f"Failed to get collection: {str(e)}")
            return "No relevant context found - collection not available."
        
        # Get embeddings for the query
        logger.info("Generating embeddings for query")
        query_embedding = await get_embeddings(query)
        if not query_embedding:
            logger.error("Failed to generate query embeddings")
            raise ValueError("Failed to generate query embeddings")
        logger.info("Successfully generated query embeddings")
        
        # Query the collection
        logger.info(f"Querying collection with k={k}")
        try:
            results = collection.query(
                query_embeddings=[query_embedding],
                n_results=k
            )
            
            if not results or not results.get("documents") or not results["documents"]:
                logger.warning("No relevant context found in vector store")
                return "No relevant context found."
            
            # Log the number of matches and their similarity scores
            documents = results.get("documents", [])
            if documents and len(documents) > 0:
                num_results = len(documents[0])
                logger.info(f"Found {num_results} relevant documents")
                
                # Check for distances (similarity scores)
                distances = results.get("distances", [])
                if distances and len(distances) > 0:
                    for i, distance in enumerate(distances[0]):
                        logger.info(f"Document {i} similarity score: {1 - distance:.4f}")
                
                # Combine the retrieved documents into a single context string
                context = "\n".join(documents[0])
                logger.info(f"Retrieved {num_results} documents from vector store")
                logger.debug("Retrieved context length: %d characters", len(context))
                return context
            
            return "No relevant context found."
        except Exception as e:
            logger.error(f"Error querying collection: {str(e)}")
            return "Error retrieving context from vector store."
            
    except Exception as e:
        logger.error("Error retrieving context from vector store", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error retrieving context: {str(e)}")
