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

# Copy requirements and install all dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Runtime stage - much smaller, only includes what's needed to run the app
FROM python:3.13-slim AS runtime
WORKDIR /app

# Install only runtime dependencies (no build tools)
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    curl \
    && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Copy installed packages from builder stage
COPY --from=builder /usr/local/lib/python3.13/site-packages /usr/local/lib/python3.13/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Copy application code
COPY ./app ./app

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Healthcheck to verify the API is up
HEALTHCHECK CMD curl --fail http://localhost:8000/health || exit 1

# Expose the API port
EXPOSE 8000

# Use a production-ready server command
CMD ["python", "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"] 