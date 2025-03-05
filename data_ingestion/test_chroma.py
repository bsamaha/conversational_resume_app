import os
from chromadb.config import Settings
import chromadb
from chromadb.api.types import IncludeEnum

# Get project root for consistent path resolution
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))

# Use the project root data directory for consistency across the application
CHROMA_DIR = os.path.join(project_root, "data/chroma")

client = chromadb.PersistentClient(
    path=CHROMA_DIR,
    settings=Settings(anonymized_telemetry=True)
)

collection = client.get_or_create_collection("resume_data")

# Use the allowed enum values instead of literal strings. Note that "data" is not an accepted value.
results = collection.get(include=[
    IncludeEnum.embeddings,
    IncludeEnum.documents,
    IncludeEnum.metadatas,
    IncludeEnum.uris  # Optionally include if you store URIs with your data
])

print("Retrieved collection data:")
print(results)