#!/bin/bash

# StreamFlow Quick Start Script
# This script helps you get StreamFlow up and running quickly
# 
 

set -e

echo "🌊 StreamFlow Quick Start"
echo "========================="

# Check if required commands are available
check_command() {
    if ! command -v $1 &> /dev/null; then
        echo "❌ $1 is not installed. Please install it first."
        exit 1
    fi
}

echo "🔍 Checking prerequisites..."
check_command "python3"
check_command "pip"
check_command "docker"
check_command "docker-compose"

# Check Python version
python_version=$(python3 --version | cut -d' ' -f2 | cut -d'.' -f1,2)
required_version="3.8"

if [ "$(printf '%s\n' "$required_version" "$python_version" | sort -V | head -n1)" != "$required_version" ]; then
    echo "❌ Python 3.8+ is required. You have Python $python_version"
    exit 1
fi

echo "✅ Prerequisites check passed"

# Create virtual environment
echo "🐍 Setting up Python virtual environment..."
if [ ! -d "venv" ]; then
    python3 -m venv venv
fi

source venv/bin/activate
echo "✅ Virtual environment activated"

# Install dependencies
echo "📦 Installing dependencies..."
pip install --upgrade pip
pip install -r requirements.txt
pip install -e .
echo "✅ Dependencies installed"

# Create environment file
echo "⚙️ Setting up environment configuration..."
if [ ! -f ".env" ]; then
    cp .env.example .env
    echo "✅ Environment file created (.env)"
    echo "📝 Please review and update the .env file with your settings"
else
    echo "✅ Environment file already exists"
fi

# Start infrastructure services
echo "🐳 Starting infrastructure services..."
docker-compose up -d rabbitmq postgres redis

echo "⏳ Waiting for services to be ready..."
sleep 30

# Initialize database
echo "🗃️ Initializing database..."
python -m streamflow.cli init-db

echo "✅ Database initialized"

# Generate JWT secret if not set
if grep -q "development-secret-key-change-in-production" .env; then
    echo "🔐 Generating JWT secret..."
    jwt_secret=$(python -c "import secrets; print(secrets.token_urlsafe(32))")
    sed -i.bak "s/development-secret-key-change-in-production.*/$jwt_secret/" .env
    echo "✅ JWT secret generated"
fi

echo ""
echo "🎉 StreamFlow is ready!"
echo ""
echo "Next steps:"
echo "1. Review the .env file and update settings as needed"
echo "2. Start the services:"
echo "   python -m streamflow.cli start --service all"
echo ""
echo "Or start individual services:"
echo "   python -m streamflow.cli start --service ingestion"
echo "   python -m streamflow.cli start --service analytics"
echo "   python -m streamflow.cli start --service dashboard"
echo ""
echo "3. Check service status:"
echo "   python -m streamflow.cli status"
echo ""
echo "4. Send test events:"
echo "   python -m streamflow.cli send-event --type web.click --count 10"
echo ""
echo "5. View the dashboard:"
echo "   Open http://localhost:8004 in your browser"
echo ""
echo "6. Check the API documentation:"
echo "   Open http://localhost:8001/docs in your browser"
echo ""
echo "📚 Documentation: https://streamflow.readthedocs.io"
echo "💬 Support: https://discord.gg/streamflow"
echo ""
echo "Happy streaming! 🚀"
