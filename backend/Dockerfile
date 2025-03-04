# Use a single-stage build approach for simplicity and consistency
FROM python:3.13-slim
WORKDIR /app

# Install build dependencies and runtime dependencies
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

# Copy requirements and install all dependencies directly from requirements.txt
COPY requirements.txt .

# Install all dependencies at once with more output for debugging
RUN pip install --no-cache-dir -r requirements.txt -v

# Clean up caches to reduce image size
RUN pip cache purge && \
    find /usr/local -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true && \
    find /usr/local -type d -name "tests" -exec rm -rf {} + 2>/dev/null || true && \
    find /usr/local -type d -name "examples" -exec rm -rf {} + 2>/dev/null || true && \
    find /usr/local -type d -name ".git" -exec rm -rf {} + 2>/dev/null || true && \
    # Clean up Rust to reduce image size
    rm -rf /root/.cargo/registry && \
    rm -rf /root/.cargo/git

# List installed packages for debugging
RUN pip list

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