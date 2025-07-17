#!/bin/bash

# StreamFlow Package Preparation Script
# This script prepares the package for publication on GitHub and PyPI
# 
 

set -e

echo "🚀 Preparing StreamFlow for publication..."

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${GREEN}✓${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}⚠${NC} $1"
}

print_error() {
    echo -e "${RED}✗${NC} $1"
}

# Check if we're in the right directory
if [ ! -f "setup.py" ] || [ ! -f "pyproject.toml" ]; then
    print_error "This script must be run from the StreamFlow root directory"
    exit 1
fi

# Check Python version
python_version=$(python3 --version 2>&1 | cut -d' ' -f2)
if ! python3 -c "import sys; exit(0 if sys.version_info >= (3, 9) else 1)"; then
    print_error "Python 3.9 or higher is required. Current version: $python_version"
    exit 1
fi

print_status "Python version check passed: $python_version"

# Install/upgrade build tools
print_status "Installing build dependencies..."
pip3 install --upgrade pip setuptools wheel build twine

# Clean previous builds
print_status "Cleaning previous builds..."
rm -rf build/ dist/ *.egg-info/ .coverage htmlcov/ .pytest_cache/

# Run tests
print_status "Running tests..."
if command -v pytest &> /dev/null; then
    python3 -m pytest tests/ -v --tb=short || {
        print_error "Tests failed. Please fix tests before publishing."
        exit 1
    }
else
    print_warning "pytest not found. Skipping tests."
fi

# Run linting
print_status "Running code quality checks..."
if command -v black &> /dev/null; then
    black --check streamflow/ || {
        print_warning "Code formatting issues found. Running black..."
        black streamflow/
    }
else
    print_warning "black not found. Skipping code formatting check."
fi

if command -v flake8 &> /dev/null; then
    flake8 streamflow/ || {
        print_warning "Linting issues found. Please review and fix."
    }
else
    print_warning "flake8 not found. Skipping linting check."
fi

# Security check
print_status "Running security checks..."
if command -v bandit &> /dev/null; then
    bandit -r streamflow/ -ll || {
        print_warning "Security issues found. Please review."
    }
else
    print_warning "bandit not found. Skipping security check."
fi

# Build package
print_status "Building package..."
python3 -m build

# Check package
print_status "Checking package integrity..."
twine check dist/* || {
    print_error "Package check failed. Please review the build output."
    exit 1
}

# Generate requirements.txt from pyproject.toml
print_status "Generating requirements.txt..."
python3 -c "
import tomllib
with open('pyproject.toml', 'rb') as f:
    data = tomllib.load(f)
deps = data['project']['dependencies']
with open('requirements.txt', 'w') as f:
    for dep in deps:
        f.write(dep + '\n')
"

# Create version file
print_status "Creating version file..."
python3 -c "
import tomllib
with open('pyproject.toml', 'rb') as f:
    data = tomllib.load(f)
version = data['project']['version']
with open('streamflow/_version.py', 'w') as f:
    f.write(f'__version__ = \"{version}\"\n')
"

# Update version in __init__.py
print_status "Updating version in __init__.py..."
python3 -c "
import tomllib
with open('pyproject.toml', 'rb') as f:
    data = tomllib.load(f)
version = data['project']['version']
with open('streamflow/__init__.py', 'r') as f:
    content = f.read()
import re
content = re.sub(r'__version__ = [\"\\'][^\"\\\']*[\"\\']', f'__version__ = \"{version}\"', content)
with open('streamflow/__init__.py', 'w') as f:
    f.write(content)
"

# Create GitHub release checklist
print_status "Creating GitHub release checklist..."
cat > RELEASE_CHECKLIST.md << 'EOF'
# StreamFlow Release Checklist

## Pre-Release
- [ ] All tests pass
- [ ] Documentation is updated
- [ ] CHANGELOG.md is updated
- [ ] Version is bumped in pyproject.toml
- [ ] Security scan passed
- [ ] Code quality checks passed

## Release
- [ ] Create GitHub release
- [ ] Upload to PyPI
- [ ] Update Docker images
- [ ] Update documentation site
- [ ] Announce on social media

## Post-Release
- [ ] Monitor for issues
- [ ] Update examples
- [ ] Plan next release
EOF

# Create Docker build script
print_status "Creating Docker build script..."
cat > scripts/build-docker.sh << 'EOF'
#!/bin/bash
set -e

echo "Building StreamFlow Docker images..."

# Build all service images
services=("ingestion" "analytics" "alerting" "dashboard" "storage")

for service in "${services[@]}"; do
    echo "Building $service service..."
    docker build -f docker/$service/Dockerfile -t streamflow-$service:latest .
    docker tag streamflow-$service:latest ghcr.io/streamflow/streamflow-$service:latest
done

echo "Docker images built successfully!"
EOF

chmod +x scripts/build-docker.sh

# Create deployment script
print_status "Creating deployment script..."
cat > scripts/deploy.sh << 'EOF'
#!/bin/bash
set -e

echo "Deploying StreamFlow..."

# Check if environment is set
if [ -z "$ENVIRONMENT" ]; then
    echo "ENVIRONMENT variable is not set. Please set it to 'staging' or 'production'"
    exit 1
fi

# Deploy based on environment
case $ENVIRONMENT in
    staging)
        echo "Deploying to staging..."
        kubectl apply -f k8s/staging/
        ;;
    production)
        echo "Deploying to production..."
        kubectl apply -f k8s/production/
        ;;
    *)
        echo "Unknown environment: $ENVIRONMENT"
        exit 1
        ;;
esac

echo "Deployment completed!"
EOF

chmod +x scripts/deploy.sh

# Create package info
print_status "Creating package information..."
python3 -c "
import tomllib
import json

with open('pyproject.toml', 'rb') as f:
    data = tomllib.load(f)

info = {
    'name': data['project']['name'],
    'version': data['project']['version'],
    'description': data['project']['description'],
    'author': data['project']['authors'][0]['name'],
    'license': data['project']['license']['text'],
    'python_requires': data['project']['requires-python'],
    'dependencies': len(data['project']['dependencies']),
    'keywords': data['project']['keywords'],
    'classifiers': data['project']['classifiers']
}

with open('package_info.json', 'w') as f:
    json.dump(info, f, indent=2)
"

# Display package information
print_status "Package information:"
cat package_info.json

echo ""
echo "🎉 StreamFlow package preparation completed successfully!"
echo ""
echo "📦 Package files created:"
echo "  - dist/streamflow-*.whl"
echo "  - dist/streamflow-*.tar.gz"
echo ""
echo "🚀 Next steps:"
echo "  1. Review the package contents"
echo "  2. Test the package in a clean environment"
echo "  3. Create a GitHub release"
echo "  4. Upload to PyPI: twine upload dist/*"
echo "  5. Update documentation"
echo ""
echo "📚 Documentation:"
echo "  - README.md - Main documentation"
echo "  - CONTRIBUTING.md - Contribution guide"
echo "  - CHANGELOG.md - Version history"
echo "  - docs/ - Detailed documentation"
echo ""
echo "🔧 Scripts created:"
echo "  - scripts/build-docker.sh - Build Docker images"
echo "  - scripts/deploy.sh - Deploy to Kubernetes"
echo "  - RELEASE_CHECKLIST.md - Release checklist"
echo ""
echo "✅ Ready for publication!"
EOF
