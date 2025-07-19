#!/bin/bash

# StreamFlow PyPI Publishing Script
# This script automates the process of publishing StreamFlow to PyPI

set -e  # Exit on any error

echo "🚀 StreamFlow PyPI Publishing Script"
echo "===================================="

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

# Check if virtual environment should be used
if [[ "$1" == "--use-venv" ]]; then
    print_status "Setting up virtual environment..."
    python3 -m venv venv
    source venv/bin/activate
    pip install --upgrade pip build twine
fi

# Check if required tools are installed
print_status "Checking required tools..."

if ! command -v python3 &> /dev/null; then
    print_error "Python 3 is not installed"
    exit 1
fi

if ! python3 -c "import build" &> /dev/null; then
    print_error "python-build is not installed. Run: pip install build"
    exit 1
fi

if ! python3 -c "import twine" &> /dev/null; then
    print_error "twine is not installed. Run: pip install twine"
    exit 1
fi

print_success "All required tools are available"

# Clean previous builds
print_status "Cleaning previous builds..."
rm -rf dist/ build/ *.egg-info/
print_success "Cleaned previous builds"

# Build the package
print_status "Building the package..."
python3 -m build

if [ $? -eq 0 ]; then
    print_success "Package built successfully"
else
    print_error "Package build failed"
    exit 1
fi

# Check the package
print_status "Checking package integrity..."
python3 -m twine check dist/*

if [ $? -eq 0 ]; then
    print_success "Package checks passed"
else
    print_error "Package checks failed"
    exit 1
fi

# Show package contents
print_status "Package contents:"
ls -la dist/

# Ask user which repository to upload to
echo ""
echo "Choose upload destination:"
echo "1) TestPyPI (recommended for testing)"
echo "2) PyPI (production)"
echo "3) Exit without uploading"
read -p "Enter your choice (1-3): " choice

case $choice in
    1)
        print_status "Uploading to TestPyPI..."
        print_warning "Make sure you have a TestPyPI account and API token configured"
        python3 -m twine upload --repository testpypi dist/*
        if [ $? -eq 0 ]; then
            print_success "Successfully uploaded to TestPyPI!"
            echo "Test installation with:"
            echo "pip install -i https://test.pypi.org/simple/ streamflow"
        else
            print_error "Upload to TestPyPI failed"
            exit 1
        fi
        ;;
    2)
        print_warning "You are about to upload to PRODUCTION PyPI!"
        read -p "Are you sure? This cannot be undone. (y/N): " confirm
        if [[ $confirm == [yY] || $confirm == [yY][eE][sS] ]]; then
            print_status "Uploading to PyPI..."
            python3 -m twine upload dist/*
            if [ $? -eq 0 ]; then
                print_success "Successfully uploaded to PyPI! 🎉"
                echo ""
                echo "Your package is now available at: https://pypi.org/project/streamflow/"
                echo "Install with: pip install streamflow"
            else
                print_error "Upload to PyPI failed"
                exit 1
            fi
        else
            print_status "Upload cancelled"
        fi
        ;;
    3)
        print_status "Exiting without uploading"
        exit 0
        ;;
    *)
        print_error "Invalid choice"
        exit 1
        ;;
esac

# Clean up virtual environment if used
if [[ "$1" == "--use-venv" ]]; then
    deactivate
    print_status "Virtual environment deactivated"
fi

print_success "Publishing script completed!"