# Build stage - includes all build dependencies
FROM python:3.13-slim AS builder
WORKDIR /app

# Install build dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    pkg-config \
    libssl-dev \
    git \
    && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Install Rust (needed for pydantic-core and other packages)
RUN curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y
ENV PATH="/root/.cargo/bin:${PATH}"

# Install pip and wheel
RUN pip install --no-cache-dir --upgrade pip wheel setuptools

# Copy requirements and prepare wheelhouse directory
COPY requirements.txt .
RUN mkdir -p /app/wheelhouse

# Add an empty file in wheelhouse to ensure directory exists for COPY command
RUN touch /app/wheelhouse/.keep

# Check for pre-built wheels in wheelhouse (will be mounted by CI)
COPY ./wheelhouse/ /app/wheelhouse/
RUN find /app/wheelhouse -type f -name "*.whl" | wc -l | grep -q "0" && echo "No wheels found, will build from scratch" || echo "Found cached wheels"

# Install dependencies - try to use wheels from wheelhouse first
RUN if [ -n "$(find /app/wheelhouse -name '*.whl' -type f 2>/dev/null)" ]; then \
      echo "Using cached wheels..." && \
      pip install --no-cache-dir --find-links=/app/wheelhouse -r requirements.txt; \
    else \
      echo "No cached wheels found, building and saving wheels..." && \
      pip wheel --wheel-dir=/app/wheelhouse -r requirements.txt && \
      pip install --no-cache-dir --find-links=/app/wheelhouse -r requirements.txt; \
    fi

# Remove unnecessary cache and files to reduce layer size
RUN pip cache purge && \
    find /usr/local -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true && \
    find /usr/local -type d -name "tests" -exec rm -rf {} + 2>/dev/null || true && \
    find /usr/local -type d -name "examples" -exec rm -rf {} + 2>/dev/null || true

# Runtime stage - much smaller, only includes what's needed to run the app
FROM python:3.13-slim AS runtime
WORKDIR /app

# Install runtime dependencies (including AWS CLI for S3 data transfer)
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    curl \
    unzip \
    && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Install AWS CLI v2
RUN curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip" && \
    unzip awscliv2.zip && \
    ./aws/install && \
    rm -rf aws awscliv2.zip

# Copy installed packages from builder stage
COPY --from=builder /usr/local/lib/python3.13/site-packages /usr/local/lib/python3.13/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Copy application code
COPY ./app ./app

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app \
    ENV=production \
    USE_S3_DATA=true \
    AUTO_UPLOAD_DATA=true \
    CHROMA_DB_PATH=/app/data/chroma

# Create needed directories
RUN mkdir -p /app/data/raw /app/data/chroma /app/data_ingestion

# Healthcheck to verify the API is up
HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
    CMD curl --fail http://localhost:8000/health || exit 1

# Expose the API port
EXPOSE 8000

# Start the FastAPI application directly with Python
# Python initialization will handle S3 data downloads through the FastAPI startup handler
CMD ["python", "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"] 