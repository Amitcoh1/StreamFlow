# StreamFlow Deployment Guide

This guide covers deploying StreamFlow using various infrastructure-as-code approaches: Terraform for AWS infrastructure, Helm charts for Kubernetes, and direct Kubernetes manifests.

## Overview

StreamFlow now uses **real data calculations** instead of mocked data:

- ✅ **Analytics Service**: Real event trends, user distribution, and source analytics from database
- ✅ **Alerting Service**: Real alert statistics, management, and notifications from database  
- ✅ **Dashboard Service**: Real metrics aggregation from storage and analytics services
- ✅ **All UI Components**: Connected to real backend APIs with live data refresh

## Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Web UI        │    │   Dashboard     │    │   Analytics     │
│   (React)       │    │   API           │    │   Engine        │
│   Port: 3000    │    │   Port: 8005    │    │   Port: 8002    │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         └───────────────────────┼───────────────────────┘
                                 │
         ┌───────────────────────┼───────────────────────┐
         │                       │                       │
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Ingestion     │    │   Storage       │    │   Alerting      │
│   Service       │    │   Service       │    │   Service       │
│   Port: 8001    │    │   Port: 8004    │    │   Port: 8003    │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         └───────────────────────┼───────────────────────┘
                                 │
┌─────────────────────────────────────────────────────────────────┐
│                    Infrastructure                               │
│  PostgreSQL │ Redis │ RabbitMQ │ Prometheus │ Grafana          │
└─────────────────────────────────────────────────────────────────┘
```

## Deployment Options

### 1. AWS Infrastructure with Terraform

Deploy complete AWS infrastructure including EKS, RDS, ElastiCache, and networking.

#### Prerequisites

- AWS CLI configured with appropriate permissions
- Terraform >= 1.0 installed
- kubectl installed

#### Deploy Infrastructure

```bash
# Navigate to terraform directory
cd terraform

# Initialize Terraform
terraform init

# Review the plan
terraform plan

# Deploy infrastructure
terraform apply

# Get kubectl config
aws eks update-kubeconfig --region us-west-2 --name streamflow-cluster
```

#### Configure Variables

Create `terraform.tfvars`:

```hcl
# Basic Configuration
project_name = "streamflow"
environment = "production"
aws_region = "us-west-2"

# Networking
vpc_cidr = "10.0.0.0/16"
public_subnet_cidrs = ["10.0.1.0/24", "10.0.2.0/24", "10.0.3.0/24"]
private_subnet_cidrs = ["10.0.4.0/24", "10.0.5.0/24", "10.0.6.0/24"]
database_subnet_cidrs = ["10.0.7.0/24", "10.0.8.0/24", "10.0.9.0/24"]

# EKS Configuration
kubernetes_version = "1.28"
node_instance_types = ["t3.large"]
node_desired_size = 3
node_max_size = 10
node_min_size = 1

# Database Configuration
db_instance_class = "db.t3.micro"
db_allocated_storage = 20
db_password = "your-secure-password"

# Redis Configuration
redis_node_type = "cache.t3.micro"
redis_auth_token = "your-redis-auth-token"

# Domain (optional)
domain_name = "yourdomain.com"
hosted_zone_id = "Z1234567890"
```

### 2. Kubernetes Deployment with Helm

Deploy StreamFlow application using Helm charts.

#### Prerequisites

- Kubernetes cluster (local or cloud)
- Helm >= 3.0 installed
- kubectl configured for your cluster

#### Deploy with Helm

```bash
# Add required Helm repositories
helm repo add bitnami https://charts.bitnami.com/bitnami
helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
helm repo add grafana https://grafana.github.io/helm-charts
helm repo update

# Navigate to helm directory
cd helm

# Install dependencies
helm dependency update streamflow/

# Deploy StreamFlow
helm install streamflow ./streamflow/ \
  --namespace streamflow \
  --create-namespace \
  --set global.storageClass=gp2 \
  --set streamflow.environment=production

# Check deployment status
kubectl get pods -n streamflow
```

#### Customize Deployment

Create `custom-values.yaml`:

```yaml
# Enable external dependencies
postgresql:
  enabled: true
  auth:
    database: "streamflow"
    username: "streamflow"
    password: "streamflow"

redis:
  enabled: true
  auth:
    password: "streamflow"

rabbitmq:
  enabled: true
  auth:
    username: "streamflow"
    password: "streamflow"

# Configure ingress
ingress:
  enabled: true
  className: "nginx"
  hosts:
    - host: streamflow.yourdomain.com
      paths:
        - path: /
          pathType: Prefix
          service: web-ui
        - path: /api
          pathType: Prefix
          service: dashboard

# Enable monitoring
prometheus:
  enabled: true
grafana:
  enabled: true
```

Deploy with custom values:

```bash
helm install streamflow ./streamflow/ \
  --namespace streamflow \
  --create-namespace \
  --values custom-values.yaml
```

### 3. Direct Kubernetes Manifests

Deploy using raw Kubernetes YAML files for maximum control.

#### Prerequisites

- Kubernetes cluster
- kubectl configured
- NGINX Ingress Controller installed
- cert-manager installed (for TLS)

#### Deploy Application

```bash
# Navigate to k8s directory
cd k8s

# Apply manifests in order
kubectl apply -f namespace.yaml
kubectl apply -f configmap.yaml
kubectl apply -f deployments.yaml
kubectl apply -f services.yaml
kubectl apply -f ingress.yaml

# Check deployment
kubectl get all -n streamflow
```

#### Install Prerequisites

```bash
# Install NGINX Ingress Controller
kubectl apply -f https://raw.githubusercontent.com/kubernetes/ingress-nginx/controller-v1.8.2/deploy/static/provider/cloud/deploy.yaml

# Install cert-manager
kubectl apply -f https://github.com/cert-manager/cert-manager/releases/download/v1.13.0/cert-manager.yaml

# Wait for components to be ready
kubectl wait --namespace ingress-nginx \
  --for=condition=ready pod \
  --selector=app.kubernetes.io/component=controller \
  --timeout=90s
```

## Configuration

### Environment Variables

Key configuration options available in ConfigMaps:

```yaml
# Database
DB_HOST: "postgres"
DB_PORT: "5432"
DB_NAME: "streamflow"
DB_USER: "streamflow"

# Redis
REDIS_HOST: "redis"
REDIS_PORT: "6379"

# Application
ENVIRONMENT: "production"
LOG_LEVEL: "INFO"
CORS_ORIGINS: "https://streamflow.local"

# Services
INGESTION_PORT: "8001"
ANALYTICS_PORT: "8002"
ALERTING_PORT: "8003"
STORAGE_PORT: "8004"
DASHBOARD_PORT: "8005"
```

### Secrets

Update secrets in `k8s/configmap.yaml` (base64 encoded):

```bash
# Encode passwords
echo -n "your-password" | base64

# Update secrets
kubectl patch secret streamflow-secrets -n streamflow \
  --type='json' \
  -p='[{"op": "replace", "path": "/data/DB_PASSWORD", "value":"'$(echo -n "new-password" | base64)'"}]'
```

## Monitoring and Observability

### Health Checks

All services expose health check endpoints:

```bash
# Check service health
kubectl get pods -n streamflow
kubectl describe pod <pod-name> -n streamflow

# Check service endpoints
curl http://streamflow.local/health
curl http://streamflow.local/api/v1/analytics/event-trends
curl http://streamflow.local/api/v1/alerts/stats
```

### Metrics and Monitoring

Access monitoring dashboards:

- **Application**: `https://streamflow.local`
- **Grafana**: `https://grafana.streamflow.local` (if enabled)
- **Prometheus**: `https://prometheus.streamflow.local` (if enabled)

### Logs

View application logs:

```bash
# View logs for specific service
kubectl logs -f deployment/streamflow-dashboard -n streamflow
kubectl logs -f deployment/streamflow-analytics -n streamflow
kubectl logs -f deployment/streamflow-alerting -n streamflow

# View logs for all pods
kubectl logs -f -l app.kubernetes.io/part-of=streamflow -n streamflow
```

## Real Data Features

### Analytics Dashboard

- **Event Trends**: Real-time event counts grouped by type and time intervals
- **User Distribution**: Device/browser analysis from actual user-agent data  
- **Top Sources**: Most active event sources with user counts
- **Event Types**: Distribution of event types from database

Access: `https://streamflow.local/analytics`

### Alerts Management

- **Real Alerts**: Active alerts from database with status tracking
- **Alert Statistics**: Counts by status (active, acknowledged, resolved)
- **Alert Actions**: Acknowledge and resolve alerts via API
- **Alert History**: Historical alert trends and patterns

Access: `https://streamflow.local/alerts`

### Dashboard Overview

- **Live Metrics**: Real event processing rates and system status
- **Event Data**: Actual event counts and distributions
- **System Health**: Real service health checks and connection status
- **Data Sources**: Active event sources with metrics

Access: `https://streamflow.local`

## Scaling

### Horizontal Pod Autoscaling

```bash
# Enable HPA for services
kubectl autoscale deployment streamflow-analytics -n streamflow \
  --cpu-percent=70 --min=2 --max=10

kubectl autoscale deployment streamflow-ingestion -n streamflow \
  --cpu-percent=70 --min=2 --max=10

# Check HPA status
kubectl get hpa -n streamflow
```

### Manual Scaling

```bash
# Scale specific services
kubectl scale deployment streamflow-analytics -n streamflow --replicas=5
kubectl scale deployment streamflow-storage -n streamflow --replicas=3

# Check scaling status
kubectl get deployments -n streamflow
```

## Troubleshooting

### Common Issues

1. **Pods not starting**: Check resource limits and node capacity
2. **Database connection errors**: Verify connection strings and credentials
3. **Ingress not working**: Check ingress controller and DNS configuration
4. **TLS certificate issues**: Verify cert-manager and Let's Encrypt configuration

### Debug Commands

```bash
# Check pod status
kubectl describe pod <pod-name> -n streamflow

# Check events
kubectl get events -n streamflow --sort-by='.lastTimestamp'

# Check ingress
kubectl describe ingress streamflow-ingress -n streamflow

# Test internal connectivity
kubectl run test-pod -n streamflow --image=busybox -it --rm -- /bin/sh
# Inside pod: wget -O- http://streamflow-dashboard:8005/health
```

### Resource Monitoring

```bash
# Check resource usage
kubectl top pods -n streamflow
kubectl top nodes

# Check resource requests/limits
kubectl describe deployment streamflow-analytics -n streamflow
```

## Security

### Network Policies

Enable network policies for enhanced security:

```yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: streamflow-network-policy
  namespace: streamflow
spec:
  podSelector:
    matchLabels:
      app.kubernetes.io/part-of: streamflow
  policyTypes:
  - Ingress
  - Egress
  ingress:
  - from:
    - namespaceSelector:
        matchLabels:
          name: streamflow
```

### Pod Security

All deployments include security contexts:

- Run as non-root user
- Read-only root filesystem
- Dropped capabilities
- Resource limits enforced

## Backup and Recovery

### Database Backups

```bash
# Manual backup
kubectl exec -n streamflow deployment/postgresql -- \
  pg_dump -U streamflow streamflow > backup.sql

# Restore
kubectl exec -n streamflow deployment/postgresql -- \
  psql -U streamflow streamflow < backup.sql
```

### Configuration Backups

```bash
# Export configurations
kubectl get configmap streamflow-config -n streamflow -o yaml > config-backup.yaml
kubectl get secret streamflow-secrets -n streamflow -o yaml > secrets-backup.yaml
```

## Production Considerations

1. **Resource Limits**: Adjust CPU/memory limits based on usage
2. **Persistent Storage**: Use appropriate storage classes for data persistence  
3. **High Availability**: Deploy across multiple availability zones
4. **Monitoring**: Set up comprehensive monitoring and alerting
5. **Security**: Enable network policies and pod security policies
6. **Backup**: Implement regular backup strategies
7. **Updates**: Plan rolling update strategies

## Support

For issues and questions:

1. Check pod logs: `kubectl logs -f <pod-name> -n streamflow`
2. Verify configurations: `kubectl get configmap -n streamflow`
3. Check resource usage: `kubectl top pods -n streamflow`
4. Review events: `kubectl get events -n streamflow`

The StreamFlow platform now provides real-time analytics with actual data calculations, comprehensive alerting, and production-ready deployment options for any Kubernetes environment. 