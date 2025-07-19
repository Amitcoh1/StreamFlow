#!/bin/bash

# StreamFlow Docker Images Build Script
# This script builds all Docker images for StreamFlow services

set -e  # Exit on any error

echo "🐳 StreamFlow Docker Images Build Script"
echo "========================================"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Configuration
VERSION=${1:-latest}
REGISTRY=${2:-""}
SERVICES=("ingestion" "analytics" "alerting" "dashboard" "storage")

print_status "Building StreamFlow Docker images with version: $VERSION"

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    print_error "Docker is not running. Please start Docker and try again."
    exit 1
fi

# Build images for each service
for service in "${SERVICES[@]}"; do
    print_status "Building $service service..."
    
    IMAGE_NAME="streamflow-$service"
    DOCKERFILE_PATH="./docker/$service/Dockerfile"
    
    if [ ! -f "$DOCKERFILE_PATH" ]; then
        print_warning "Dockerfile not found for $service at $DOCKERFILE_PATH. Skipping..."
        continue
    fi
    
    # Build the image
    if docker build -t "$IMAGE_NAME:$VERSION" -f "$DOCKERFILE_PATH" .; then
        print_success "Built $IMAGE_NAME:$VERSION"
        
        # Tag with registry if provided
        if [ -n "$REGISTRY" ]; then
            REGISTRY_TAG="$REGISTRY/$IMAGE_NAME:$VERSION"
            docker tag "$IMAGE_NAME:$VERSION" "$REGISTRY_TAG"
            print_success "Tagged as $REGISTRY_TAG"
        fi
    else
        print_error "Failed to build $IMAGE_NAME:$VERSION"
        exit 1
    fi
done

# Build using docker-compose (alternative method)
print_status "Building services using docker-compose..."
if docker-compose build; then
    print_success "Docker Compose build completed successfully"
else
    print_error "Docker Compose build failed"
    exit 1
fi

# Show built images
print_status "Built images:"
docker images | grep streamflow

# Option to push to registry
if [ -n "$REGISTRY" ]; then
    echo ""
    read -p "Push images to registry $REGISTRY? (y/N): " push_confirm
    if [[ $push_confirm == [yY] || $push_confirm == [yY][eE][sS] ]]; then
        for service in "${SERVICES[@]}"; do
            IMAGE_NAME="streamflow-$service"
            REGISTRY_TAG="$REGISTRY/$IMAGE_NAME:$VERSION"
            
            print_status "Pushing $REGISTRY_TAG..."
            if docker push "$REGISTRY_TAG"; then
                print_success "Pushed $REGISTRY_TAG"
            else
                print_error "Failed to push $REGISTRY_TAG"
            fi
        done
    fi
fi

print_success "Docker image build process completed! 🎉"
echo ""
echo "Usage:"
echo "  Local: docker-compose up"
echo "  Individual: docker run streamflow-ingestion:$VERSION"
if [ -n "$REGISTRY" ]; then
    echo "  Registry: docker pull $REGISTRY/streamflow-ingestion:$VERSION"
fi