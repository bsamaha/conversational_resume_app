# Conversational Resume & Portfolio Chatbot (CRPC)

Conversational Resume & Portfolio Chatbot (CRPC) is an AI-powered chatbot that lets you interactively explore your resume and portfolio via a conversational interface powered by Retrieval-Augmented Generation (RAG). The application integrates a scalable FastAPI backend with semantic search using ChromaDB and OpenAI embeddings, alongside a modern React-based frontend, all containerized via Docker for straightforward deployment.

## Features

- 🤖 **Interactive Chat Interface:** Engage in natural conversations with the AI assistant.
- 🔍 **RAG Technology:** Combines context retrieval with OpenAI API responses for accurate information.
- 🚀 **Scalable Backend:** Powered by FastAPI for robust performance and easy extensibility.
- ⚛️ **Modern Frontend:** A user-friendly interface built with React.
- 🐳 **Containerized Deployment:** Seamlessly run the full stack with Docker Compose.
- 📊 **Chat History Storage:** Automatically saves chat logs to AWS S3 for analysis and record keeping.

## Prerequisites

- Python 3.9+
- Node.js 14+
- Docker & Docker Compose (optional but recommended)
- An OpenAI API key
- AWS credentials for S3 storage (optional)

## Project Structure

```
conversational-resume/
├── backend/              # FastAPI backend
├── frontend/             # React frontend
├── data_ingestion/       # Data processing scripts & ingestion tool
└── data/                 # Data storage (raw documents, ChromaDB data)
    ├── raw/              # Original markdown resume files
    └── chroma/           # Vector database storage
```

The project uses a standardized data directory structure:
- All data is stored in the `data/` directory at the project root
- Resume documents and markdown files go in `data/raw/`
- The vector database is stored in `data/chroma/`
- This single data location is referenced consistently across all components

## Setup

1. **Clone the Repository:**
   ```bash
   git clone https://github.com/yourusername/conversational-resume.git
   cd conversational-resume
   ```

2. **Configure Environment Variables:**
   Copy the sample environment file and update with your settings:
   ```bash
   cp .env.example .env
   ```
   Edit the `.env` file with the following settings:
   - OpenAI API key
   - AWS credentials (for chat history storage)
   - Other configuration options

   **AWS Credentials Setup:**
   For chat log storage in S3, you'll need to provide AWS credentials in the `.env` file:
   ```
   # AWS credentials 
   AWS_ACCESS_KEY_ID=your_access_key_id
   AWS_SECRET_ACCESS_KEY=your_secret_access_key
   AWS_SESSION_TOKEN=your_session_token  # Only required for temporary credentials
   AWS_REGION=your_region  # e.g., us-east-1
   AWS_S3_BUCKET_NAME=your_bucket_name
   ```

   **Notes on AWS credentials:**
   - For permanent credentials (starting with AKIA), only access key and secret key are needed
   - For temporary credentials (starting with ASIA), you must include the session token
   - Consider using instance profiles/IAM roles in production environments

3. **Install Backend Dependencies:**
   ```bash
   cd backend
   pip install -r requirements.txt
   ```

4. **Install Frontend Dependencies:**
   ```bash
   cd ../frontend
   npm install
   ```

5. **Process Your Resume Data:**
   Place your resume and portfolio documents in the `data/raw/` directory, then run:
   ```bash
   cd ../data_ingestion
   pip install -r requirements.txt
   python ingest.py
   ```

## Running the Application

### Using Docker (Recommended)

Docker Compose simplifies running the full stack. Build and start all services with:
```bash
docker-compose up --build
```
After the build completes, access the services at:
- **Frontend:** [http://localhost:3000](http://localhost:3000)
- **Backend API:** [http://localhost:8000](http://localhost:8000)

### Manual Setup

#### Running the Backend (FastAPI)
Start the backend API using Uvicorn:
```bash
cd backend
uvicorn app.main:app --reload
```
This will start the API at [http://localhost:8000](http://localhost:8000).

#### Running the Frontend
For local development of the frontend, you have two options:

- **Development Mode (React):**
  ```bash
  cd frontend
  npm start
  ```
  This starts the React development server (typically at [http://localhost:3000](http://localhost:3000)).

- **Serving Static Files Locally:**
  If you prefer serving static files without the React development setup:
  ```bash
  cd frontend
  python -m http.server 8000
  ```
  Then open your browser at [http://localhost:8000](http://localhost:8000).

> **Note:** Ensure the frontend's API calls (e.g., in `main.js`) correctly point to your running backend instance (default is `http://localhost:8000/api`).

## How It Works

1. **Backend API & Conversation Chain:**
   - The FastAPI backend processes incoming queries and leverages a conversational chain to maintain context.
   - It retrieves relevant context from the ChromaDB vector store and responds using LangChain integrated with OpenAI's models.

2. **Retrieval-Augmented Generation (RAG):**
   - The chatbot uses RAG, combining user queries with context extracted from your resume data for more detailed and accurate answers.

3. **Frontend Interface:**
   - A streamlined form collects user information before starting the chat session
   - A modern, responsive React frontend displays both user and chatbot messages dynamically.

4. **Chat History Storage:**
   - When a user ends their session, the chat history is automatically saved to AWS S3
   - Data is organized in a data-lake compatible structure for easy analysis
   - Chat logs include metadata about the user, conversation duration, and message count

5. **Containerization:**
   - Docker containerizes both backend and frontend, ensuring a consistent runtime environment across different setups.

## Advanced RAG Techniques

The CRPC implements several advanced Retrieval-Augmented Generation (RAG) techniques to enhance the quality and relevance of AI responses:

### High-Quality Document Embeddings

The system utilizes several sophisticated techniques to improve document embeddings:

1. **Context-Enhanced Document Representation**
   - Each document chunk is enriched with metadata before embedding
   - Section headers and document structure are incorporated into the vector representation
   - This helps the model understand both content and context, improving retrieval precision

2. **Advanced Entity Extraction**
   - Specialized parsing extracts entities like dates, locations, skills, and organizations
   - These entities are stored as metadata, enabling more precise filtering
   - Pattern recognition identifies key professional experiences and qualifications

3. **Optimized Vector Similarity**
   - Cosine similarity is used for semantic matching between queries and documents
   - This approach focuses on directional similarity rather than magnitude
   - Results in more semantically accurate retrieval for professional context questions

### Efficient Processing Pipeline

1. **Intelligent Document Chunking**
   - Markdown-aware splitting preserves the hierarchical structure of resume documents
   - Chunks maintain headings and relevant context, preserving the relationship between sections
   - Overlap strategy ensures concepts that cross chunk boundaries are properly represented

2. **Batch Processing with Rate Limiting**
   - Documents are processed in optimized batches to balance throughput and API limitations
   - Built-in rate limiting prevents throttling issues when processing larger document sets
   - Improves reliability and cost-effectiveness of the embedding generation process

3. **Robust Error Handling**
   - Comprehensive validation ensures type compatibility with the vector database
   - Lists and complex types are properly converted to database-compatible formats
   - Ensures consistent performance without metadata-related failures

### Query Enhancement

1. **Query Classification and Expansion**
   - Incoming queries are classified by type (e.g., technical expertise, career history)
   - Retrieval parameters are adjusted based on query classification
   - Enables more relevant document retrieval for different question types

2. **Similarity Threshold Filtering**
   - Retrieved documents are filtered by minimum similarity score
   - Prevents irrelevant information from being included in the context
   - Improves response quality by focusing only on highly relevant content

These techniques collectively transform a basic RAG system into a sophisticated retrieval engine that captures the nuanced relationships in professional documents, enabling more accurate, contextually relevant responses to user inquiries.

## API Endpoints

The backend provides the following key endpoints:

- **POST /api/chat** - Send chat messages to the AI assistant
  ```json
  {
    "query": "User's question",
    "language": "en",
    "thread_id": "unique-session-id"
  }
  ```

- **POST /api/save-chat** - Save chat history to S3
  ```json
  {
    "session_id": "unique-session-id",
    "user_info": {
      "name": "User Name",
      "email": "user@example.com",
      "companyName": "Company Name",
      "companyType": "",
      "purpose": "purpose_value",
      "jobRole": "job_role_value"
    },
    "messages": [
      {
        "content": "Message content",
        "is_user": true,
        "timestamp": "2023-01-01T12:00:00Z"
      }
    ]
  }
  ```

## Contributing

1. Fork the repository.
2. Create your feature branch.
3. Commit your changes.
4. Push to the branch.
5. Open a new Pull Request.

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for further details. 