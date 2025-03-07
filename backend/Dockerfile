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

# Copy and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

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
    zip \
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

# Copy startup script
COPY ./startup.sh /app/startup.sh
RUN chmod +x /app/startup.sh

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV ENV=production
ENV USE_S3_DATA=true
ENV AUTO_UPLOAD_DATA=true

# Create needed directories
RUN mkdir -p /app/data/raw /app/data/chroma /app/data_ingestion

# Healthcheck to verify the API is up
HEALTHCHECK CMD curl --fail http://localhost:8000/health || exit 1

# Expose the API port
EXPOSE 8000

# Use our startup script
CMD ["/app/startup.sh"] 