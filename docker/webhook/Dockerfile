FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better Docker layer caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . ./streamflow/

# Copy setup files
COPY setup.py .
COPY README.md .
COPY requirements.txt .

# Install StreamFlow in development mode
RUN pip install -e .

# Create non-root user
RUN useradd -m -u 1001 webhook && chown -R webhook:webhook /app

# Create directory for certificates
RUN mkdir -p /etc/certs && chown webhook:webhook /etc/certs

USER webhook

# Expose webhook port (HTTPS)
EXPOSE 8443

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f -k https://localhost:8443/health || exit 1

# Run the webhook service
CMD ["python", "-m", "streamflow.services.webhook.main"] 