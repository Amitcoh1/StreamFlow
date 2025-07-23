#!/bin/bash

# StreamFlow Webhook Test Script
# Tests the webhook by deploying a sample application and verifying enhancement

set -e

echo "🧪 Testing StreamFlow Kubernetes Mutating Webhook..."

# Check if webhook is deployed
if ! kubectl get mutatingwebhookconfigurations streamflow-webhook &> /dev/null; then
    echo "❌ StreamFlow webhook not found. Please deploy it first:"
    echo "   ./scripts/deploy-webhook.sh"
    exit 1
fi

# Create test namespace
echo "📁 Creating test namespace..."
kubectl create namespace webhook-test --dry-run=client -o yaml | kubectl apply -f -

# Deploy test application
echo "🚀 Deploying test application..."
cat <<EOF | kubectl apply -f -
apiVersion: apps/v1
kind: Deployment
metadata:
  name: webhook-test-app
  namespace: webhook-test
spec:
  replicas: 1
  selector:
    matchLabels:
      app: webhook-test-app
  template:
    metadata:
      labels:
        app: webhook-test-app
    spec:
      containers:
      - name: nginx
        image: nginx:alpine
        ports:
        - containerPort: 80
---
apiVersion: v1
kind: Service
metadata:
  name: webhook-test-service
  namespace: webhook-test
spec:
  selector:
    app: webhook-test-app
  ports:
  - port: 80
    targetPort: 80
  type: ClusterIP
EOF

# Wait for deployment
echo "⏳ Waiting for deployment..."
kubectl wait --for=condition=available --timeout=60s deployment/webhook-test-app -n webhook-test

# Check if webhook annotations were added
echo ""
echo "🔍 Checking webhook enhancements..."

# Check deployment annotations
echo "📋 Deployment annotations:"
kubectl get deployment webhook-test-app -n webhook-test -o jsonpath='{.metadata.annotations}' | jq '.' 2>/dev/null || echo "No annotations found"

# Check deployment labels
echo "📋 Deployment labels:"
kubectl get deployment webhook-test-app -n webhook-test -o jsonpath='{.metadata.labels}' | jq '.' 2>/dev/null || echo "No labels found"

# Check service annotations
echo "📋 Service annotations:"
kubectl get service webhook-test-service -n webhook-test -o jsonpath='{.metadata.annotations}' | jq '.' 2>/dev/null || echo "No annotations found"

# Check pod template annotations
echo "📋 Pod template annotations:"
kubectl get deployment webhook-test-app -n webhook-test -o jsonpath='{.spec.template.metadata.annotations}' | jq '.' 2>/dev/null || echo "No annotations found"

# Verify StreamFlow annotations
echo ""
echo "🎯 Verification Results:"

# Check for StreamFlow monitoring annotation
if kubectl get deployment webhook-test-app -n webhook-test -o jsonpath='{.metadata.annotations.streamflow\.io/monitoring}' | grep -q "enabled"; then
    echo "✅ StreamFlow monitoring annotation found"
else
    echo "❌ StreamFlow monitoring annotation missing"
fi

# Check for StreamFlow managed label
if kubectl get deployment webhook-test-app -n webhook-test -o jsonpath='{.metadata.labels.streamflow\.io/managed}' | grep -q "true"; then
    echo "✅ StreamFlow managed label found"
else
    echo "❌ StreamFlow managed label missing"
fi

# Check for injection timestamp
if kubectl get deployment webhook-test-app -n webhook-test -o jsonpath='{.metadata.annotations.streamflow\.io/injected-at}' | grep -q "20"; then
    echo "✅ Injection timestamp found"
else
    echo "❌ Injection timestamp missing"
fi

echo ""
echo "🧹 Cleaning up test resources..."
kubectl delete namespace webhook-test

echo ""
echo "🎉 Webhook test completed!"
echo ""
echo "📊 Expected enhancements:"
echo "   - streamflow.io/monitoring: enabled"
echo "   - streamflow.io/metrics-path: /metrics"
echo "   - streamflow.io/health-path: /health"
echo "   - streamflow.io/managed: true"
echo "   - Injection timestamp" 