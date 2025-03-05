import logging
from langchain_chroma import Chroma
from chromadb.config import Settings as ChromaSettings
from app.core.config import get_settings
from app.core.embeddings import get_embeddings
from fastapi import HTTPException
import chromadb
from chromadb.api.types import Include, IncludeEnum
from typing import Dict, Any, List, Optional, Union, cast, Tuple, Literal
import os
import re

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

async def get_relevant_context(query: str, k: int = 5) -> str:
    """
    Retrieve relevant context from the ChromaDB vector store using semantic search.
    
    Args:
        query: The user's query string
        k: Number of documents to retrieve (increased from 3 to 5 for better coverage)
        
    Returns:
        A formatted string containing relevant context with metadata
    """
    try:
        logger.info(f"Retrieving context for query: {query}")
        
        # Preprocess and enhance the query to improve retrieval
        enhanced_query, query_type = preprocess_query(query)
        logger.info(f"Enhanced query: {enhanced_query}")
        logger.info(f"Detected query type: {query_type}")
        
        # Adjust search parameters based on query type
        if query_type == "basic_info":
            k = max(k, 7)  # Increase k for basic info to get more context
        elif query_type == "technical_expertise":
            k = max(k, 5)  # Standard k for technical questions
        elif query_type == "career_history":
            k = max(k, 6)  # Slightly more context for career history
        elif query_type == "followup_question":
            # For follow-up questions, we want to be more inclusive to catch relevant context
            k = max(k, 8)  # Get more documents for follow-up questions to ensure relevant context is included
        else:  # "general"
            k = max(k, 4)  # Default number for general questions
            
        client = get_chroma_client()
        
        try:
            collection = client.get_collection("resume_data")
            logger.info("Successfully retrieved collection 'resume_data'")
            
            # Check if the collection has the expected dimensionality
            expected_dim = settings.get_embedding_dimension()
            collection_info = collection.get(limit=1, include=[])  # Get info without actual data
            
            # If the collection exists but is empty, we can't check dimensions
            # This is fine because new documents will use the configured dimension
            if collection.count() == 0:
                logger.warning("Collection is empty, cannot verify embedding dimensions.")
            
        except Exception as e:
            logger.error(f"Failed to get collection: {str(e)}")
            return "No relevant context found - collection not available."
        
        # Get embeddings for the query using our simplified embeddings function
        logger.info("Generating embeddings for query")
        query_embedding = await get_embeddings(enhanced_query)
        if not query_embedding:
            logger.error("Failed to generate query embeddings")
            raise ValueError("Failed to generate query embeddings")
        logger.info("Successfully generated query embeddings")
        
        # Try-except block specifically for the query operation
        try:
            # Query the collection with a higher k for initial filtering
            # We'll get more candidates and filter later based on relevance
            initial_k = min(k * 2, 12)  # Get more candidates than needed, but cap at 12
            logger.info(f"Querying collection with initial_k={initial_k}")
            
            # Query collection with all necessary data
            results = collection.query(
                query_embeddings=[query_embedding],
                n_results=initial_k,
                include=["documents", "distances", "metadatas"]  # type: ignore
            )
            
            # Safely extract results with proper null handling
            documents = results.get("documents", [[]])
            distances = results.get("distances", [[]])
            metadatas = results.get("metadatas", [[]])
            
            # Check if we have valid results
            if not documents or len(documents) == 0 or len(documents[0]) == 0:
                logger.warning("No relevant context found in vector store")
                return "No relevant context found."
            
            # Extract the first set of results (from the first query embedding)
            docs = documents[0]
            dists = distances[0] if distances and len(distances) > 0 else []
            metas = metadatas[0] if metadatas and len(metadatas) > 0 else []
            
            num_results = len(docs)
            logger.info(f"Found {num_results} candidate documents")
            
            # Calculate similarity scores (higher is better)
            similarity_scores = [1 - dist for dist in dists]
            
            # Use adaptive thresholds based on query type
            if query_type == "basic_info":
                min_similarity = 0.2  # Lower threshold for basic information
            elif query_type == "technical_expertise":
                min_similarity = 0.25  # Slightly higher for technical questions
            elif query_type == "career_history":
                min_similarity = 0.2  # Lower threshold for career history
            elif query_type == "followup_question":
                # For follow-up questions, we want to be more inclusive to catch relevant context
                min_similarity = 0.15  # Lower threshold for follow-up questions
            else:  # "general"
                min_similarity = 0.15  # Lowest threshold for general questions

            logger.info(f"Using similarity threshold of {min_similarity} for query type '{query_type}'")
            filtered_results = []
            
            # Zip with safe handling of different length lists
            for i in range(len(docs)):
                doc = docs[i]
                score = similarity_scores[i] if i < len(similarity_scores) else 0
                meta = {}
                
                # Safely extract metadata
                if i < len(metas):
                    meta_item = metas[i]
                    if isinstance(meta_item, dict):
                        meta = meta_item
                
                logger.info(f"Document {i} similarity score: {score:.4f}")
                
                if score >= min_similarity:
                    # Format document with metadata if available
                    formatted_doc = format_document_with_metadata(doc, meta)
                    filtered_results.append((formatted_doc, score))
                else:
                    logger.info(f"Filtered out document {i} with low similarity: {score:.4f}")
            
            # Sort by similarity score and take top k
            filtered_results.sort(key=lambda x: x[1], reverse=True)
            top_results = filtered_results[:k]
            
            if not top_results:
                logger.warning("No documents passed the similarity threshold - falling back to best available matches")
                
                # Fallback: Get the top k results regardless of threshold, but ensure they have a minimum similarity
                floor_threshold = 0.1  # Absolute minimum threshold
                fallback_results = []
                
                for i in range(len(docs)):
                    doc = docs[i]
                    score = similarity_scores[i] if i < len(similarity_scores) else 0
                    meta = {}
                    
                    # Only consider documents above the floor threshold
                    if score >= floor_threshold:
                        # Safely extract metadata
                        if i < len(metas):
                            meta_item = metas[i]
                            if isinstance(meta_item, dict):
                                meta = meta_item
                        
                        # Format document with metadata
                        formatted_doc = format_document_with_metadata(doc, meta)
                        fallback_results.append((formatted_doc, score))
                
                fallback_results.sort(key=lambda x: x[1], reverse=True)
                top_results = fallback_results[:k]
                
                if not top_results:
                    logger.warning("No documents passed even the floor threshold")
                    return "No sufficiently relevant context found."
                
                logger.info(f"Using {len(top_results)} results from fallback mechanism")
            
            # Combine the retrieved documents into a single context string
            context_parts = [doc for doc, _ in top_results]
            context = "\n\n---\n\n".join(context_parts)
            
            logger.info(f"Retrieved {len(top_results)} filtered documents from vector store")
            logger.info(f"Final context length: {len(context)} characters")
            
            return context
            
        except Exception as e:
            error_msg = str(e)
            logger.error(f"Error querying collection: {error_msg}")
            
            # Check specifically for dimension mismatch errors
            if "dimension" in error_msg.lower() and "match" in error_msg.lower():
                # Get the collection's actual dimension from the error message if possible
                dim_match = re.search(r'dimensionality (\d+)', error_msg)
                collection_dim = int(dim_match.group(1)) if dim_match else "unknown"
                
                logger.error(
                    f"Embedding dimension mismatch detected: "
                    f"Query uses {len(query_embedding)}-dimensional vectors, but "
                    f"collection has {collection_dim}-dimensional vectors."
                )
                
                admin_msg = (
                    f"CONFIGURATION ERROR: Embedding model mismatch between query and collection. "
                    f"Current model ({settings.embedding_model}) produces {len(query_embedding)}-dimensional vectors, "
                    f"but your collection contains {collection_dim}-dimensional vectors. "
                    f"To fix this, you need to rebuild the collection with the current embedding model "
                    f"or change EMBEDDING_MODEL in your .env file to match the model used to build the collection."
                )
                
                logger.error(admin_msg)
                return "No relevant context found - embedding dimension mismatch."
            
            # For other errors, return a generic message
            return "No relevant context found due to retrieval error."
            
    except Exception as e:
        logger.error("Error retrieving context from vector store", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error retrieving context: {str(e)}")

def format_document_with_metadata(document: str, metadata: Dict[str, Any]) -> str:
    """
    Format the document with its metadata to provide enriched context.
    
    Args:
        document: The document text
        metadata: Metadata dictionary associated with the document
        
    Returns:
        Formatted document with metadata
    """
    formatted_parts = []
    
    # Extract core metadata fields (if present)
    source = metadata.get("source", "")
    section = metadata.get("section", "")
    job_title = metadata.get("job_title", "")
    company = metadata.get("company", "")
    date_range = metadata.get("date_range", "")
    technologies = metadata.get("technologies", "")
    
    # Add source information if available (e.g., "From Resume: Work Experience")
    if source:
        if section:
            formatted_parts.append(f"From {source}: {section}")
        else:
            formatted_parts.append(f"From {source}")
    
    # For job experiences, format with clear title, company, and dates
    if job_title and company:
        job_header = f"{job_title} at {company}"
        if date_range:
            job_header += f" ({date_range})"
        formatted_parts.append(job_header)
    
    # Add technologies explicitly if available
    if technologies:
        formatted_parts.append(f"Technologies used: {technologies}")
    
    # Special handling for career history documents
    if section and "experience" in section.lower() or "career" in section.lower():
        timeline_context = ""
        if job_title:
            timeline_context += f"Position: {job_title}. "
        if company:
            timeline_context += f"Company: {company}. "
        if date_range:
            timeline_context += f"Timeline: {date_range}. "
        if timeline_context:
            formatted_parts.append(timeline_context)

    # Extract technical information from the document text if not provided in metadata
    if not technologies and document:
        tech_indicators = ["using", "leveraging", "built with", "developed in", "implemented", "tech stack", "frameworks", "languages"]
        tech_terms = ["Python", "JavaScript", "TypeScript", "React", "Angular", "Vue", "Node.js", "SQL", "NoSQL", "MySQL", 
                     "PostgreSQL", "MongoDB", "Redis", "Azure", "AWS", "GCP", "Docker", "Kubernetes", "Terraform", 
                     "CI/CD", "Jenkins", "GitHub Actions", "REST API", "GraphQL", "Apache", "Iceberg", "Spark", 
                     "Kafka", "RabbitMQ", "IoT Hub", "Event Hub", "serverless"]
        
        detected_techs = []
        for term in tech_terms:
            if term.lower() in document.lower():
                detected_techs.append(term)
        
        if detected_techs:
            formatted_parts.append(f"Relevant technologies detected: {', '.join(detected_techs)}")
    
    # Add the document text
    formatted_parts.append(document)
    
    # Add any other metadata that might be valuable (exclude what we've already used)
    used_keys = {"source", "section", "job_title", "company", "date_range", "technologies"}
    for key, value in metadata.items():
        if key not in used_keys and value:
            formatted_parts.append(f"{key.capitalize()}: {value}")
    
    # Join all parts with double line breaks for clear separation
    return "\n\n".join(formatted_parts)

def preprocess_query(query: str) -> tuple[str, str]:
    """
    Preprocess and enhance the query to improve retrieval performance.
    
    Args:
        query: The original user query
        
    Returns:
        A tuple containing (enhanced query, query type)
    """
    # Lowercase for easier pattern matching
    query_lower = query.lower()
    
    # Detect query type based on patterns
    query_type = "general"
    enhanced_query = query
    
    # Check for timeline/chronology-related questions
    timeline_patterns = [
        "when", "timeline", "how long", "duration", "period", "years", 
        "worked", "joined", "left", "before", "after", "during", "dates",
        "chronology", "history", "previous", "next", "last job", "first job"
    ]
    company_names = [
        "enchanted rock", "entergy", "u-blox", "ublox", "occidental", "oxy", 
        "clutch sports", "marine corps", "marines"
    ]
    career_history_patterns = [
        "career", "work history", "work experience", "job history", "employment", 
        "roles", "positions", "companies", "employers", "jobs"
    ]
    
    # Enhanced timeline detection
    if any(pattern in query_lower for pattern in timeline_patterns):
        query_type = "career_history"
        # Add timeline-specific enhancement
        enhanced_query = f"timeline {query} job chronology work history dates"
        
    # Enhanced company-specific detection
    elif any(company in query_lower for company in company_names):
        query_type = "career_history"
        # Extract which company is being asked about
        mentioned_companies = [company for company in company_names if company in query_lower]
        company_enhancement = " ".join(mentioned_companies)
        enhanced_query = f"{query} {company_enhancement} work experience job responsibilities"
        
    # Career history detection
    elif any(pattern in query_lower for pattern in career_history_patterns):
        query_type = "career_history"
        enhanced_query = f"{query} work history employment timeline job chronology"
    
    # Check for follow-up questions which often lack context on their own
    followup_patterns = [
        "what did you do there", "how was it", "tell me more", "more details", 
        "what about", "and then", "after that", "what next", "what else", 
        "responsibilities", "tell me about", "what was your role"
    ]
    
    if any(pattern in query_lower for pattern in followup_patterns):
        query_type = "followup_question"
        # For follow-up questions, we'll expand with key company names and role keywords
        # to maximize the chance of retrieving relevant context
        enhanced_query = f"{query} work experience role position responsibilities companies Enchanted Rock Entergy u-blox Occidental Petroleum Clutch Sports career history"
    
    # Technical expertise detection remains the same
    technical_patterns = [
        "skills", "technologies", "programming", "technical", "software", 
        "expertise", "proficiency", "qualification", "stack", "tools",
        "machine learning", "artificial intelligence", "ai", "ml", "data",
        "cloud", "aws", "azure", "iot", "apis", "microservices", "architecture"
    ]
    
    if any(pattern in query_lower for pattern in technical_patterns):
        query_type = "technical_expertise"
        enhanced_query = f"{query} skills technologies expertise proficiency qualifications technical"
    
    # Basic info detection remains the same
    basic_info_patterns = [
        "who", "name", "about", "introduction", "background", "summary", 
        "education", "contact", "email", "phone", "location", "experience", 
        "overview", "bio", "profile", "portfolio"
    ]
    
    if any(pattern in query_lower for pattern in basic_info_patterns) and query_type == "general":
        query_type = "basic_info"
        enhanced_query = f"{query} professional summary background profile overview"
        
    return enhanced_query, query_type

def classify_query(query: str) -> str:
    """
    Classify the query into predefined categories to tailor retrieval strategy.
    
    Args:
        query: Normalized user query
        
    Returns:
        Query type classification
    """
    # Define keywords for different query types
    basic_info_keywords = ["who", "what", "where", "when", "contact", "email", "phone", 
                          "location", "address", "age", "old", "born", "education", 
                          "university", "college", "degree", "graduate"]
    
    technical_keywords = ["skills", "technologies", "programming", "languages", "tools",
                         "technical", "expertise", "competencies", "proficient", 
                         "experience with", "knowledge of", "aws", "azure", "cloud", 
                         "iot", "devops", "terraform", "kubernetes", "docker", "python",
                         "java", "c#", "kafka", "sql", "database", "architecture"]
    
    career_keywords = ["work", "job", "position", "role", "career", "experience", 
                      "company", "employer", "project", "accomplishment", "achievement",
                      "responsibility", "manager", "lead", "director", "architect",
                      "history", "previous", "oxy", "occidental", "u-blox", "entergy"]
    
    # Count keyword matches for each category
    basic_count = sum(1 for word in basic_info_keywords if word in query)
    technical_count = sum(1 for word in technical_keywords if word in query)
    career_count = sum(1 for word in career_keywords if word in query)
    
    # Determine the category with the most matches
    if basic_count > technical_count and basic_count > career_count:
        return "basic_info"
    elif technical_count > basic_count and technical_count > career_count:
        return "technical_expertise"
    elif career_count > basic_count and career_count > technical_count:
        return "career_history"
    else:
        # Default to a general query if no clear category emerges
        return "general"

def expand_query(query: str, query_type: str) -> str:
    """
    Expand the query with additional relevant terms based on its type.
    
    Args:
        query: Original user query
        query_type: Classification of the query
        
    Returns:
        Expanded query with additional context terms
    """
    # Handle first job questions better
    if any(term in query for term in ["first job", "start", "career"]):
        return query + " first job career start beginning initial position employment work history"
    
    # Handle basic info queries like name, location, etc.
    if "name" in query:
        return query + " name full name identity resume"
    
    if any(term in query for term in ["from", "live", "location"]):
        return query + " location residence city state country hometown"
    
    # Handle specific company queries - important for your example
    if "enchanted rock" in query.lower():
        return query + " enchanted rock employment experience job position role responsibilities company work"
    
    # Specific company pattern matching with explicit context terms
    company_pattern = r"(experience|work|job|time).*(at|with|for) ([a-zA-Z0-9\s&-]+)"
    company_match = re.search(company_pattern, query)
    if company_match:
        company = company_match.group(3).strip()
        return f"{query} {company} role position title responsibilities achievements work history experience"
    
    # Expand skill-related queries
    if query_type == "technical_expertise":
        return f"{query} skills experience expertise proficient competent technologies tools"
    
    # Expand career history queries
    elif query_type == "career_history":
        return f"{query} work experience history position role companies employers"
    
    # Expand education queries
    elif "education" in query or "degree" in query or "university" in query or "college" in query:
        return f"{query} education university college degree graduate study major field"
        
    # Add general terms for basic info queries
    elif query_type == "basic_info":
        return f"{query} information personal resume profile background"
    
    # If nothing specific, return original
    return query
