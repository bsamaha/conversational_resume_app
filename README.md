# Conversational Resume & Portfolio Chatbot (CRPC)

Conversational Resume & Portfolio Chatbot (CRPC) is an AI-powered chatbot that lets you interactively explore your resume and portfolio via a conversational interface powered by Retrieval-Augmented Generation (RAG). The application integrates a scalable FastAPI backend with semantic search using ChromaDB and OpenAI embeddings, alongside a modern React-based frontend, all containerized via Docker for straightforward deployment.

## Quick Start

1. **Clone and setup:**
   ```bash
   git clone https://github.com/yourusername/conversational-resume.git
   cd conversational-resume
   cp .env.example .env
   # Edit .env with your OpenAI API key and other settings
   ```

2. **Add your resume data:**
   - Create a `data/raw` directory
   - Add your resume/portfolio markdown files to this directory

3. **Run with Docker (recommended):**
   ```bash
   docker-compose up --build
   ```
   
4. **Access the application:**
   - Frontend: http://localhost:3000
   - Backend API: http://localhost:8000

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
├── .github/              # GitHub-specific files
│   └── workflows/        # GitHub Actions workflow files
│       └── ecr-deploy.yml # CI/CD workflow for ECR deployment
├── backend/              # FastAPI backend
│   ├── app/              # Application code
│   │   ├── api/          # API endpoints
│   │   ├── core/         # Core application logic
│   │   │   └── config.py # Configuration with Parameter Store integration
│   │   ├── models/       # Data models
│   │   ├── schemas/      # Request/response schemas
│   │   ├── services/     # Business logic services
│   │   └── utils/        # Utility functions
│   ├── tests/            # Backend tests
│   └── requirements.txt  # Python dependencies
├── frontend/             # React frontend
│   ├── src/              # Source code
│   │   ├── components/   # React components
│   │   ├── services/     # API services
│   │   ├── styles/       # CSS styles
│   │   └── types/        # TypeScript type definitions
│   ├── public/           # Static assets
│   └── package.json      # Node.js dependencies
├── data_ingestion/       # Data processing scripts & ingestion tool
│   ├── ingest.py         # Main ingestion script
│   ├── test_vector_db.py # Utility for testing vector database
│   ├── test_chroma.py    # Test for ChromaDB functionality
│   └── requirements.txt  # Python dependencies
├── docker-compose.yml    # Docker configuration for all services
├── .env.example          # Example environment variables
├── docs/                 # Documentation
│   └── ci_cd_workflow.md # CI/CD workflow documentation
├── scripts/              # Helper scripts
│   ├── create_ecr_repos.sh # Script to create ECR repositories
│   └── setup_parameter_store.sh # Script to set up Parameter Store secrets
└── data/                 # Data storage (raw documents, ChromaDB data)
    ├── raw/              # Original markdown resume files
    └── chroma/           # Vector database storage
```

The project uses a standardized data directory structure:
- All data is stored in the `data/` directory at the project root
- Resume documents and markdown files go in `data/raw/`
- The vector database is stored in `data/chroma/`
- This single data location is referenced consistently across all components
- Empty `.gitkeep` files ensure the directory structure is maintained in Git while ignoring the actual data files

## Infrastructure

This repository contains only the application code. The infrastructure-as-code (Terraform) has been moved to a separate repository for better separation of concerns and to follow infrastructure best practices.

## Continuous Integration/Deployment

This project uses GitHub Actions for CI/CD to automatically build and push Docker images to Amazon ECR when code is updated.

### Prerequisites for GitHub Actions

1. **AWS ECR Repositories**:
   - Create two repositories in Amazon ECR:
     - One for the backend image
     - One for the frontend image
   - You can use the included helper script to create these repositories:
     ```bash
     # Make the script executable if needed
     chmod +x scripts/create_ecr_repos.sh
     
     # Run the script
     ./scripts/create_ecr_repos.sh
     ```

2. **IAM User for GitHub Actions**:
   - Create an IAM user with permissions to push to ECR
   - Attach the `AmazonECR-FullAccess` policy or create a custom policy with these minimum permissions:
     ```json
     {
       "Version": "2012-10-17",
       "Statement": [
         {
           "Effect": "Allow",
           "Action": [
             "ecr:CompleteLayerUpload",
             "ecr:GetAuthorizationToken",
             "ecr:UploadLayerPart",
             "ecr:InitiateLayerUpload",
             "ecr:BatchCheckLayerAvailability",
             "ecr:PutImage"
           ],
           "Resource": "*"
         }
       ]
     }
     ```

3. **GitHub Repository Secrets**:
   - Add the following secrets to your GitHub repository:
     - `AWS_ACCESS_KEY_ID`: Your IAM user's access key
     - `AWS_SECRET_ACCESS_KEY`: Your IAM user's secret key
     - `AWS_REGION`: The AWS region your ECR repositories are in
     - `ECR_BACKEND_REPOSITORY`: The name of your backend ECR repository
     - `ECR_FRONTEND_REPOSITORY`: The name of your frontend ECR repository
   - See the [GitHub Actions documentation](.github/workflows/README.md) for more details

### Workflow Behavior

The GitHub Actions workflow:
- Triggers when code is pushed to the `main` branch (affecting backend, frontend, or Docker configuration)
- Builds Docker images for both the backend and frontend
- Tags images with both the commit SHA and `latest`
- Pushes the images to their respective ECR repositories
- Can be manually triggered using the GitHub Actions interface

For a detailed explanation of the CI/CD workflow with diagrams, see [CI/CD Workflow Documentation](docs/ci_cd_workflow.md).

## Secret Management

This project uses AWS Systems Manager Parameter Store for managing secrets in production environments. This provides a secure, cost-effective way to store and access sensitive information.

### Parameter Store Structure

The application expects the following parameters to be available in Parameter Store:

- `OPENAI_API_KEY`: Your OpenAI API key
- `CONVERSATIONAL_RESUME_AWS_ACCESS_KEY_ID`: AWS access key used by the application
- `CONVERSATIONAL_RESUME_AWS_ACCESS_KEY_SECRET`: AWS secret key used by the application

### Environment-Based Configuration

The application uses different configuration sources based on the environment:

- **Development**: Uses `.env` file or environment variables
- **Staging/Production**: Automatically fetches secrets from Parameter Store while falling back to environment variables if needed

### Creating Parameters in Parameter Store

Use the provided helper script to easily set up your Parameter Store secrets:

```bash
# Make the script executable
chmod +x scripts/setup_parameter_store.sh

# Run the script
./scripts/setup_parameter_store.sh
```

This interactive script will:
- Prompt you for your secrets
- Store them in Parameter Store as SecureString parameters
- Optionally create an IAM policy for access

Alternatively, you can manually create the parameters using the AWS CLI:

```bash
# Store OpenAI API key
aws ssm put-parameter \
    --name "OPENAI_API_KEY" \
    --value "your-api-key" \
    --type "SecureString"

# Store AWS credentials
aws ssm put-parameter \
    --name "CONVERSATIONAL_RESUME_AWS_ACCESS_KEY_ID" \
    --value "your-access-key" \
    --type "SecureString"

aws ssm put-parameter \
    --name "CONVERSATIONAL_RESUME_AWS_ACCESS_KEY_SECRET" \
    --value "your-secret-key" \
    --type "SecureString"
```

### Required IAM Permissions

For the application to access Parameter Store, ensure your IAM role has these permissions:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "ssm:GetParameter",
        "ssm:GetParameters",
        "ssm:DescribeParameters"
      ],
      "Resource": "arn:aws:ssm:*:*:parameter/*"
    }
  ]
}
```

### Troubleshooting Parameter Store Access

If you encounter issues with Parameter Store access:

1. **Verify IAM Permissions**: Ensure your IAM user or role has the permissions listed above
2. **Check Parameter Names**: Verify that parameters exist with exactly the names expected by the application
3. **AWS Profiles**: If using multiple AWS profiles, make sure the correct profile is active (`AWS_PROFILE` environment variable)
4. **Permission Propagation**: IAM permission changes can take 5-10 minutes to propagate
5. **Local Fallback**: In development, the application will fall back to using values from your `.env` file if Parameter Store access fails

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

## CI/CD and Data Handling

### GitHub Actions Workflow

The GitHub Actions workflow:
- Triggers when code is pushed to the `main` branch (affecting backend, frontend, or Docker configuration)
- Builds Docker images for both the backend and frontend
- Tags images with both the commit SHA and `latest`
- Pushes the images to their respective ECR repositories
- Can be manually triggered using the GitHub Actions interface

For a detailed explanation of the CI/CD workflow with diagrams, see [CI/CD Workflow Documentation](docs/ci_cd_workflow.md).

### S3 Data Handling

The application can store and retrieve ChromaDB vector embeddings from S3, which is particularly useful in production deployments:

#### How It Works
1. **Local Development:** 
   - By default, the application uses local storage for ChromaDB data
   - Set `USE_S3_DATA=false` in your `.env` file

2. **Production Environment:**
   - When deploying to production, set `USE_S3_DATA=true`
   - The container will attempt to download ChromaDB data from S3 on startup
   - If no data is found, it will process raw data from `data/raw` (if available)
   - With `AUTO_UPLOAD_DATA=true`, newly generated ChromaDB data is automatically uploaded to S3

#### Setting Up S3 Data Storage

1. **Create an S3 Bucket:**
   ```bash
   aws s3 mb s3://your-app-data-bucket
   ```

2. **Upload Initial ChromaDB Data:**
   ```bash
   chmod +x scripts/upload_chroma_to_s3.sh
   ./scripts/upload_chroma_to_s3.sh your-app-data-bucket production
   ```

3. **Configure GitHub Secrets:**
   - Add `S3_DATA_BUCKET` to your repository secrets
   - Ensure your IAM user has S3 permissions

4. **Required IAM Permissions:**
   ```json
   {
     "Version": "2012-10-17",
     "Statement": [
       {
         "Effect": "Allow",
         "Action": [
           "s3:GetObject",
           "s3:PutObject",
           "s3:ListBucket"
         ],
         "Resource": [
           "arn:aws:s3:::your-app-data-bucket",
           "arn:aws:s3:::your-app-data-bucket/*"
         ]
       }
     ]
   }
   ```

#### Windows Compatibility

For Windows users, we provide PowerShell alternatives to the bash scripts:

1. **Using PowerShell for S3 Uploads:**
   ```powershell
   # Run with execution policy bypass
   powershell -ExecutionPolicy Bypass -File .\scripts\upload_chroma_to_s3.ps1 your-bucket-name production
   ```

2. **Alternative for Git Bash on Windows:**
   If you prefer Git Bash but don't have the `zip` command, use the Windows-friendly script that uses 7-Zip:
   ```bash
   chmod +x scripts/upload_chroma_to_s3_win.sh
   ./scripts/upload_chroma_to_s3_win.sh your-bucket-name production
   ```
   Note: This requires 7-Zip to be installed at the default location (`C:\Program Files\7-Zip\`).

#### Troubleshooting S3 Data Uploads

- **AWS Credentials**: Ensure your AWS credentials are configured correctly with `aws configure`
- **Permissions**: Your IAM user needs `s3:PutObject` and `s3:GetObject` permissions
- **Region**: Make sure the AWS region configured matches your S3 bucket's region
- **AWS Profile**: If you use multiple AWS profiles, specify the correct one with `--profile` or set the `AWS_PROFILE` environment variable

## Development Notes

### Dependency Management

The application uses specific version constraints in `requirements.txt` files to ensure compatibility:

1. **Version Pinning**:
   - Core dependencies have specific versions pinned (e.g., `langchain==0.3.20`)
   - This prevents unexpected breaking changes when dependencies update

2. **Important Constraints**:
   - `pydantic-settings>=2.4.0`: Required for compatibility with `langchain-community==0.3.19`
   - `langchain-core==0.3.41`: Ensures compatibility with other LangChain components
   - `openai==1.65.2`: Provides stability when interacting with the OpenAI API

If you encounter dependency conflicts:
- Check version constraints between `pydantic-settings` and `langchain-community`
- Update both backend and data_ingestion requirements.txt files to maintain consistency
- Run `pip install --upgrade pip` before installing dependencies

### Debugging

1. **Parameter Store Errors**: 
   - If you see errors accessing AWS Parameter Store, check the [Troubleshooting Parameter Store Access](#troubleshooting-parameter-store-access) section
   - The application will fall back to environment variables in development

2. **ChromaDB Data Issues**:
   - If your responses seem incorrect, verify ChromaDB data is properly loaded
   - Check logs for any errors during data loading
   - Try rebuilding the ChromaDB data by running the ingestion script

3. **Docker Issues**:
   - Use `docker-compose logs backend` to view detailed backend logs
   - The startup script includes detailed logging of each step 