#!/bin/bash

# StreamFlow Webhook Deployment Script
# Deploys the Kubernetes mutating webhook to automatically enhance services

set -e

echo "🚀 Deploying StreamFlow Kubernetes Mutating Webhook..."

# Check if kubectl is available
if ! command -v kubectl &> /dev/null; then
    echo "❌ kubectl not found. Please install kubectl first."
    exit 1
fi

# Check if we're connected to a cluster
if ! kubectl cluster-info &> /dev/null; then
    echo "❌ No Kubernetes cluster connection. Please configure kubectl first."
    exit 1
fi

# Generate certificates if they don't exist
if [ ! -d "./webhook-certs" ]; then
    echo "🔐 Generating TLS certificates..."
    ./scripts/generate-webhook-certs.sh
else
    echo "📋 Using existing certificates from ./webhook-certs/"
fi

# Build webhook Docker image
echo "🏗️ Building webhook Docker image..."
docker build -t streamflow-webhook:latest -f docker/webhook/Dockerfile .

# For local development with kind/minikube, load image
if kubectl cluster-info | grep -q "kind\|minikube"; then
    echo "📦 Loading image into local cluster..."
    if command -v kind &> /dev/null && kubectl cluster-info | grep -q "kind"; then
        kind load docker-image streamflow-webhook:latest
    elif command -v minikube &> /dev/null && kubectl cluster-info | grep -q "minikube"; then
        minikube image load streamflow-webhook:latest
    fi
fi

# Deploy to Kubernetes
echo "☸️ Deploying to Kubernetes..."

# Create namespace
kubectl apply -f k8s/webhook/namespace.yaml

# Create RBAC
kubectl apply -f k8s/webhook/rbac.yaml

# Create certificate secret
kubectl apply -f webhook-certs/webhook-certs-secret.yaml

# Deploy webhook service
kubectl apply -f k8s/webhook/service.yaml
kubectl apply -f k8s/webhook/deployment.yaml

# Wait for deployment to be ready
echo "⏳ Waiting for webhook deployment to be ready..."
kubectl wait --for=condition=available --timeout=300s deployment/streamflow-webhook -n streamflow-webhook

# Apply webhook configuration
echo "🔗 Applying mutating webhook configuration..."
kubectl apply -f webhook-certs/mutating-webhook-config.yaml

# Verify deployment
echo "✅ Verifying deployment..."
kubectl get pods -n streamflow-webhook
kubectl get services -n streamflow-webhook

echo ""
echo "🎉 StreamFlow Webhook deployed successfully!"
echo ""
echo "📋 The webhook will automatically:"
echo "   - Add StreamFlow monitoring annotations to new deployments"
echo "   - Add StreamFlow labels for service discovery"
echo "   - Inject metrics and health check paths"
echo "   - Skip system namespaces and already-annotated objects"
echo ""
echo "🧪 To test the webhook:"
echo "   kubectl create deployment test-app --image=nginx"
echo "   kubectl get deployment test-app -o yaml | grep streamflow"
echo ""
echo "🔧 To disable webhook for a namespace:"
echo "   kubectl label namespace <namespace> streamflow.io/webhook=disabled"
echo ""
echo "🗑️ To remove the webhook:"
echo "   kubectl delete mutatingwebhookconfiguration streamflow-webhook"
echo "   kubectl delete namespace streamflow-webhook" 