#!/bin/bash

# StreamFlow Startup Script
# This script helps you get StreamFlow up and running quickly

set -e

echo "🌊 StreamFlow Startup Script"
echo "============================"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

print_header() {
    echo -e "${BLUE}[STEP]${NC} $1"
}

# Check if Docker is installed
check_docker() {
    if ! command -v docker &> /dev/null; then
        print_error "Docker is not installed. Please install Docker first."
        exit 1
    fi
    
    if ! command -v docker-compose &> /dev/null; then
        print_error "Docker Compose is not installed. Please install Docker Compose first."
        exit 1
    fi
    
    print_status "Docker and Docker Compose are available"
}

# Check if Python is installed
check_python() {
    if ! command -v python3 &> /dev/null; then
        print_error "Python 3 is not installed. Please install Python 3.8+ first."
        exit 1
    fi
    
    python_version=$(python3 --version | cut -d' ' -f2)
    print_status "Python version: $python_version"
}

# Create .env file if it doesn't exist
create_env_file() {
    if [ ! -f .env ]; then
        print_status "Creating .env file..."
        cp .env.example .env
        print_status ".env file created from .env.example"
    else
        print_status ".env file already exists"
    fi
}

# Start infrastructure services
start_infrastructure() {
    print_header "Starting infrastructure services..."
    
    print_status "Starting RabbitMQ, PostgreSQL, and Redis..."
    docker-compose up -d rabbitmq postgres redis
    
    print_status "Waiting for services to be ready..."
    sleep 10
    
    # Check if services are healthy
    for service in rabbitmq postgres redis; do
        if docker-compose ps $service | grep -q "Up"; then
            print_status "$service is running"
        else
            print_warning "$service might not be ready yet"
        fi
    done
}

# Install Python dependencies
install_dependencies() {
    print_header "Installing Python dependencies..."
    
    if [ ! -d ".venv" ]; then
        print_status "Creating virtual environment..."
        python3 -m venv .venv
    fi
    
    print_status "Activating virtual environment..."
    source .venv/bin/activate
    
    print_status "Installing dependencies..."
    pip install -r requirements.txt
    pip install -e .
    
    print_status "Dependencies installed successfully"
}

# Initialize database
init_database() {
    print_header "Initializing database..."
    
    # Wait for PostgreSQL to be ready
    max_attempts=30
    attempt=0
    
    while [ $attempt -lt $max_attempts ]; do
        if docker-compose exec -T postgres pg_isready -U streamflow; then
            print_status "PostgreSQL is ready"
            break
        fi
        
        print_status "Waiting for PostgreSQL... (attempt $((attempt+1))/$max_attempts)"
        sleep 2
        attempt=$((attempt+1))
    done
    
    if [ $attempt -eq $max_attempts ]; then
        print_error "PostgreSQL is not ready after $max_attempts attempts"
        exit 1
    fi
    
    # Run migrations
    print_status "Running database migrations..."
    # Note: Uncomment the following line when Alembic is configured
    # alembic upgrade head
    print_status "Database initialization complete"
}

# Start StreamFlow services
start_services() {
    print_header "Starting StreamFlow services..."
    
    print_status "Building Docker images..."
    docker-compose build
    
    print_status "Starting all services..."
    docker-compose up -d
    
    print_status "Waiting for services to start..."
    sleep 15
    
    # Check service health
    services=("ingestion" "analytics" "alerting" "dashboard" "storage")
    for service in "${services[@]}"; do
        if docker-compose ps $service | grep -q "Up"; then
            print_status "$service is running"
        else
            print_warning "$service might not be ready yet"
        fi
    done
}

# Show service URLs
show_urls() {
    print_header "Service URLs:"
    echo ""
    echo "📊 Dashboard API:        http://localhost:8004"
    echo "🔌 Ingestion API:        http://localhost:8001"
    echo "📈 Analytics Service:    http://localhost:8002"
    echo "🚨 Alerting Service:     http://localhost:8003"
    echo "💾 Storage Service:      http://localhost:8005"
    echo ""
    echo "🐰 RabbitMQ Management:  http://localhost:15672 (admin/admin123)"
    echo "🐘 PostgreSQL:           localhost:5432 (streamflow/streamflow123)"
    echo "🗄️  Redis:               localhost:6379"
    echo ""
    echo "📚 Health Checks:"
    echo "   curl http://localhost:8001/health"
    echo "   curl http://localhost:8002/health"
    echo "   curl http://localhost:8003/health"
    echo "   curl http://localhost:8004/health"
    echo "   curl http://localhost:8005/health"
}

# Test the system
test_system() {
    print_header "Testing system..."
    
    # Wait a bit for services to be fully ready
    sleep 10
    
    # Test ingestion service
    print_status "Testing ingestion service..."
    if curl -s http://localhost:8001/health > /dev/null; then
        print_status "✅ Ingestion service is healthy"
    else
        print_warning "⚠️  Ingestion service might not be ready yet"
    fi
    
    # Test analytics service
    print_status "Testing analytics service..."
    if curl -s http://localhost:8002/health > /dev/null; then
        print_status "✅ Analytics service is healthy"
    else
        print_warning "⚠️  Analytics service might not be ready yet"
    fi
    
    # Test dashboard service
    print_status "Testing dashboard service..."
    if curl -s http://localhost:8004/health > /dev/null; then
        print_status "✅ Dashboard service is healthy"
    else
        print_warning "⚠️  Dashboard service might not be ready yet"
    fi
}

# Show example usage
show_example() {
    print_header "Example Usage:"
    echo ""
    echo "Send a test event:"
    echo 'curl -X POST http://localhost:8001/events \
  -H "Content-Type: application/json" \
  -d "{
    \"type\": \"user.click\",
    \"source\": \"web_app\",
    \"data\": {
      \"user_id\": \"user123\",
      \"page\": \"/dashboard\",
      \"element\": \"button.submit\"
    },
    \"severity\": \"low\",
    \"tags\": [\"frontend\", \"test\"]
  }"'
    echo ""
    echo "Create an alert rule:"
    echo 'curl -X POST http://localhost:8003/alerts/rules \
  -H "Content-Type: application/json" \
  -d "{
    \"name\": \"Test Alert\",
    \"condition\": \"data.user_id == '\''user123'\''\",
    \"window_seconds\": 300,
    \"channels\": [\"email\"]
  }"'
    echo ""
    echo "Get real-time metrics:"
    echo "curl http://localhost:8004/metrics/realtime"
}

# Main execution
main() {
    print_header "StreamFlow Setup Starting..."
    
    check_docker
    check_python
    create_env_file
    start_infrastructure
    install_dependencies
    init_database
    start_services
    
    echo ""
    print_status "🎉 StreamFlow is now running!"
    echo ""
    
    show_urls
    test_system
    show_example
    
    echo ""
    print_status "For more information, check out:"
    echo "  📖 README.md"
    echo "  🚀 GETTING_STARTED.md"
    echo "  💡 examples/usage_examples.py"
    echo ""
    print_status "To stop StreamFlow: docker-compose down"
    print_status "To view logs: docker-compose logs -f"
    echo ""
    print_status "Happy streaming! 🌊"
}

# Handle script arguments
case "${1:-}" in
    --help|-h)
        echo "StreamFlow Startup Script"
        echo ""
        echo "Usage: $0 [OPTIONS]"
        echo ""
        echo "Options:"
        echo "  --help, -h     Show this help message"
        echo "  --stop         Stop all services"
        echo "  --restart      Restart all services"
        echo "  --logs         Show service logs"
        echo "  --status       Show service status"
        echo ""
        exit 0
        ;;
    --stop)
        print_status "Stopping StreamFlow services..."
        docker-compose down
        print_status "Services stopped"
        exit 0
        ;;
    --restart)
        print_status "Restarting StreamFlow services..."
        docker-compose restart
        print_status "Services restarted"
        exit 0
        ;;
    --logs)
        print_status "Showing service logs..."
        docker-compose logs -f
        exit 0
        ;;
    --status)
        print_status "Service status:"
        docker-compose ps
        exit 0
        ;;
    "")
        main
        ;;
    *)
        print_error "Unknown option: $1"
        echo "Use --help for usage information"
        exit 1
        ;;
esac
