#!/bin/bash

# StreamFlow Webhook Certificate Generation Script
# Generates TLS certificates for the Kubernetes mutating webhook

set -e

NAMESPACE="streamflow-webhook"
SERVICE_NAME="streamflow-webhook"
CERT_DIR="./webhook-certs"

echo "🔐 Generating TLS certificates for StreamFlow webhook..."

# Create certificate directory
mkdir -p $CERT_DIR

# Generate private key
echo "📋 Generating private key..."
openssl genrsa -out $CERT_DIR/tls.key 2048

# Generate certificate signing request
echo "📋 Generating certificate signing request..."
cat > $CERT_DIR/csr.conf <<EOF
[req]
distinguished_name = req_distinguished_name
req_extensions = v3_req
prompt = no

[req_distinguished_name]
C = US
ST = CA
L = San Francisco
O = StreamFlow
OU = Webhook
CN = $SERVICE_NAME.$NAMESPACE.svc

[v3_req]
keyUsage = keyEncipherment, dataEncipherment
extendedKeyUsage = serverAuth
subjectAltName = @alt_names

[alt_names]
DNS.1 = $SERVICE_NAME
DNS.2 = $SERVICE_NAME.$NAMESPACE
DNS.3 = $SERVICE_NAME.$NAMESPACE.svc
DNS.4 = $SERVICE_NAME.$NAMESPACE.svc.cluster.local
EOF

# Generate certificate signing request
openssl req -new -key $CERT_DIR/tls.key -out $CERT_DIR/tls.csr -config $CERT_DIR/csr.conf

# Generate self-signed certificate (for development)
echo "📋 Generating self-signed certificate..."
openssl x509 -req -in $CERT_DIR/tls.csr -signkey $CERT_DIR/tls.key -out $CERT_DIR/tls.crt -days 365 -extensions v3_req -extfile $CERT_DIR/csr.conf

# Create CA bundle (self-signed for development)
cp $CERT_DIR/tls.crt $CERT_DIR/ca-bundle.crt

# Generate base64 encoded CA bundle for Kubernetes
CA_BUNDLE=$(cat $CERT_DIR/ca-bundle.crt | base64 | tr -d '\n')

echo "✅ Certificates generated successfully!"
echo "📁 Certificate files:"
echo "   - Private Key: $CERT_DIR/tls.key"
echo "   - Certificate: $CERT_DIR/tls.crt"
echo "   - CA Bundle: $CERT_DIR/ca-bundle.crt"
echo ""
echo "🔗 CA Bundle for Kubernetes (base64):"
echo "$CA_BUNDLE"
echo ""

# Create Kubernetes secret manifest
echo "📝 Creating Kubernetes secret manifest..."
cat > $CERT_DIR/webhook-certs-secret.yaml <<EOF
apiVersion: v1
kind: Secret
metadata:
  name: webhook-certs
  namespace: $NAMESPACE
type: kubernetes.io/tls
data:
  tls.crt: $(cat $CERT_DIR/tls.crt | base64 | tr -d '\n')
  tls.key: $(cat $CERT_DIR/tls.key | base64 | tr -d '\n')
EOF

# Create MutatingWebhookConfiguration with the CA bundle
echo "📝 Creating MutatingWebhookConfiguration manifest..."
cat > $CERT_DIR/mutating-webhook-config.yaml <<EOF
apiVersion: admissionregistration.k8s.io/v1
kind: MutatingWebhookConfiguration
metadata:
  name: streamflow-webhook
webhooks:
- name: streamflow.webhook.io
  clientConfig:
    service:
      name: $SERVICE_NAME
      namespace: $NAMESPACE
      path: "/mutate"
    caBundle: $CA_BUNDLE
  rules:
  - operations: ["CREATE", "UPDATE"]
    apiGroups: ["apps", ""]
    apiVersions: ["v1"]
    resources: ["deployments", "services"]
  namespaceSelector:
    matchExpressions:
    - key: streamflow.io/webhook
      operator: NotIn
      values: ["disabled"]
  admissionReviewVersions: ["v1", "v1beta1"]
  sideEffects: None
  failurePolicy: Fail
EOF

echo "✅ Kubernetes manifests created:"
echo "   - Secret: $CERT_DIR/webhook-certs-secret.yaml"
echo "   - MutatingWebhookConfiguration: $CERT_DIR/mutating-webhook-config.yaml"
echo ""
echo "🚀 Next steps:"
echo "   1. Deploy the webhook service: kubectl apply -f k8s/webhook/"
echo "   2. Create the certificate secret: kubectl apply -f $CERT_DIR/webhook-certs-secret.yaml"
echo "   3. Apply the webhook configuration: kubectl apply -f $CERT_DIR/mutating-webhook-config.yaml" 