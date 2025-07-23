#!/bin/bash

# StreamFlow Webhook Entrypoint Script
set -e

echo "🚀 Starting StreamFlow Mutating Webhook..."

# Debug information
echo "📋 Debug info:"
echo "   Working directory: $(pwd)"
echo "   Python path: $PYTHONPATH"
echo "   Python version: $(python --version)"

# List contents of /app
echo "📁 Contents of /app:"
ls -la /app/

# Check if StreamFlow is installed
echo "🔍 Checking Python package installation:"
python -c "import sys; print('Python path:', sys.path)" || echo "Failed to get Python path"

echo "🔍 Testing StreamFlow import:"
python -c "import streamflow; print('StreamFlow package found at:', streamflow.__file__)" || echo "StreamFlow import failed"

echo "🔍 Testing webhook module import:"
python -c "import streamflow.services.webhook.main; print('Webhook module imported successfully')" || echo "Webhook module import failed"

# Check if certificates exist
if [ ! -f "/etc/certs/tls.key" ] || [ ! -f "/etc/certs/tls.crt" ]; then
    echo "❌ SSL certificates not found in /etc/certs/"
    exit 1
fi

echo "✅ SSL certificates found"

# Get configuration from environment
WEBHOOK_PORT=${WEBHOOK_PORT:-8443}
WEBHOOK_CERT_DIR=${WEBHOOK_CERT_DIR:-/etc/certs}

echo "📋 Configuration:"
echo "   Port: $WEBHOOK_PORT"
echo "   Cert Dir: $WEBHOOK_CERT_DIR"

# Start the webhook using Python directly
echo "🔗 Starting webhook server..."
cd /app
exec python -c "
import uvicorn
from streamflow.services.webhook.main import app
uvicorn.run(
    app,
    host='0.0.0.0',
    port=$WEBHOOK_PORT,
    ssl_keyfile='$WEBHOOK_CERT_DIR/tls.key',
    ssl_certfile='$WEBHOOK_CERT_DIR/tls.crt',
    log_level='info'
)
" 