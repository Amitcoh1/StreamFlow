# Multi-stage Dockerfile for Analytics Service
 

FROM python:3.11-slim AS builder

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir --user -r requirements.txt

# Production stage
FROM python:3.11-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    libpq5 \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user
RUN groupadd -r streamflow && useradd -r -g streamflow streamflow

# Set working directory
WORKDIR /app

# Copy Python dependencies from builder stage
COPY --from=builder /root/.local /home/streamflow/.local

# Copy application code
COPY . ./streamflow/
COPY setup.py .
COPY README.md .
COPY requirements.txt .

# Install the package
RUN pip install -e . && \
    mkdir -p /app/logs && \
    chown -R streamflow:streamflow /app

# Switch to non-root user
USER streamflow

# Add local Python packages to PATH
ENV PATH=/home/streamflow/.local/bin:$PATH

# Run the application
CMD ["uvicorn", "streamflow.services.analytics.main:app", "--host", "0.0.0.0", "--port", "8002"]
