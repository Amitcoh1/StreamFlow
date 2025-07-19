# StreamFlow 🌊

A **production-ready real-time analytics platform** for event processing, monitoring, and insights. StreamFlow provides comprehensive analytics dashboards, intelligent alerting, and scalable data processing with **real-time calculations** from live data sources.

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python](https://img.shields.io/badge/Python-3.8%2B-blue.svg)](https://python.org)
[![React](https://img.shields.io/badge/React-18.0%2B-61DAFB.svg)](https://reactjs.org)
[![Kubernetes](https://img.shields.io/badge/Kubernetes-1.28%2B-326CE5.svg)](https://kubernetes.io)
[![Docker](https://img.shields.io/badge/Docker-Ready-2496ED.svg)](https://docker.com)

## ✨ Features

### 📊 **Real-Time Analytics**
- **Live Event Trends**: Real-time event processing with time-series analysis
- **User Distribution**: Device and browser analytics from actual user-agent data
- **Source Analytics**: Top event sources with user counts and activity metrics
- **Event Type Analysis**: Distribution and patterns of different event types
- **Interactive Dashboards**: Modern React UI with live data refresh

### 🚨 **Intelligent Alerting**
- **Real Alert Management**: Active alerts from database with status tracking
- **Alert Statistics**: Live counts by status (active, acknowledged, resolved)
- **Alert Actions**: Acknowledge and resolve alerts via REST API
- **Alert History**: Historical trends and pattern analysis
- **Multi-Channel Notifications**: Email, Slack, and webhook support

### 🔄 **Event Processing**
- **High-Throughput Ingestion**: Scalable event ingestion with validation
- **Stream Processing**: Real-time event analysis and aggregation
- **Data Storage**: Optimized PostgreSQL storage with JSON serialization
- **Message Queuing**: RabbitMQ for reliable event distribution
- **Caching Layer**: Redis for high-performance data access

### 🏗️ **Production Infrastructure**
- **Multiple Deployment Options**: Terraform (AWS), Helm (K8s), Direct Manifests
- **Auto-Scaling**: Horizontal Pod Autoscaling based on CPU/memory
- **Health Monitoring**: Comprehensive health checks and metrics
- **Security**: RBAC, network policies, TLS encryption, and secure defaults
- **High Availability**: Multi-replica deployments with rolling updates

## 🏛️ Architecture

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

## 🚀 Quick Start

### Local Development

```bash
# Clone the repository
git clone https://github.com/your-org/streamflow.git
cd streamflow

# Start infrastructure services
./start.sh

# Install dependencies
pip install -r requirements.txt
cd web-ui && npm install

# Start services
python -m streamflow.services.storage.main &
python -m streamflow.services.analytics.main &
python -m streamflow.services.alerting.main &
python -m streamflow.services.dashboard.main &
python -m streamflow.services.ingestion.main &

# Start web UI
cd web-ui && npm start
```

Access the application at `http://localhost:3000`

### Production Deployment

Choose your preferred deployment method:

#### Option 1: AWS with Terraform
```bash
cd terraform
terraform init
terraform apply
```

#### Option 2: Kubernetes with Helm
```bash
helm install streamflow ./helm/streamflow/ \
  --namespace streamflow --create-namespace
```

#### Option 3: Direct Kubernetes
```bash
kubectl apply -f k8s/
```

See [DEPLOYMENT.md](./DEPLOYMENT.md) for detailed instructions.

## 📱 User Interface

### Analytics Dashboard
- **Real-time event trends** with customizable time intervals
- **User distribution** by device type and browser
- **Top event sources** with activity metrics
- **Event type analysis** with visual breakdowns
- **Export functionality** for data analysis

### Alerts Management
- **Active alerts** with status tracking and management
- **Alert statistics** by severity and status
- **Bulk operations** for acknowledging and resolving alerts
- **Alert history** and trend analysis
- **Real-time notifications** via WebSocket

### System Dashboard
- **Live metrics** showing system performance
- **Service health** monitoring and status
- **Event processing** rates and throughput
- **Resource utilization** and scaling metrics
- **WebSocket connections** for real-time updates

## 🔧 Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `DB_HOST` | PostgreSQL host | `localhost` |
| `DB_PORT` | PostgreSQL port | `5432` |
| `DB_NAME` | Database name | `streamflow` |
| `REDIS_HOST` | Redis host | `localhost` |
| `REDIS_PORT` | Redis port | `6379` |
| `RABBITMQ_HOST` | RabbitMQ host | `localhost` |
| `LOG_LEVEL` | Logging level | `INFO` |
| `ENVIRONMENT` | Environment | `development` |

### Service Ports

| Service | Port | Description |
|---------|------|-------------|
| Ingestion | 8001 | Event ingestion API |
| Analytics | 8002 | Analytics processing |
| Alerting | 8003 | Alert management |
| Storage | 8004 | Data storage API |
| Dashboard | 8005 | Main dashboard API |
| Web UI | 3000 | React frontend |

## 📊 API Documentation

### Event Ingestion
```bash
# Create event
POST /api/v1/events
{
  "type": "web.click",
  "source": "web-app",
  "data": {"page": "/dashboard", "user_id": "123"},
  "user_id": "user123"
}
```

### Analytics
```bash
# Get event trends
GET /api/v1/analytics/event-trends?hours=24&interval_minutes=60

# Get user distribution
GET /api/v1/analytics/user-distribution

# Get top sources
GET /api/v1/analytics/top-sources?limit=10
```

### Alerts
```bash
# Get alerts
GET /api/v1/alerts?status=active&limit=50

# Acknowledge alert
POST /api/v1/alerts/{alert_id}/acknowledge

# Resolve alert
POST /api/v1/alerts/{alert_id}/resolve
```

See [API.md](./docs/API.md) for complete API documentation.

## 🧪 Testing

```bash
# Run backend tests
python -m pytest tests/

# Run frontend tests
cd web-ui && npm test

# Run integration tests
python -m pytest tests/test_comprehensive.py

# Load testing
python examples/usage_examples.py
```

## 🔐 Security

- **Authentication**: JWT-based authentication for API access
- **Authorization**: Role-based access control (RBAC)
- **Encryption**: TLS/SSL for all communication
- **Input Validation**: Comprehensive request validation
- **Security Headers**: CORS, CSP, and other security headers
- **Network Policies**: Kubernetes network segmentation
- **Pod Security**: Non-root containers with minimal privileges

## 📈 Monitoring & Observability

### Health Checks
All services expose health endpoints at `/health` and `/ready`

### Metrics
- **Prometheus integration** for metrics collection
- **Grafana dashboards** for visualization
- **Custom metrics** for business intelligence
- **Performance monitoring** and alerting

### Logging
- **Structured logging** with JSON format
- **Centralized logging** with ELK stack integration
- **Log aggregation** across all services
- **Error tracking** and debugging

## 🔄 Scaling

### Horizontal Scaling
```bash
# Scale specific services
kubectl scale deployment streamflow-analytics --replicas=5
kubectl scale deployment streamflow-storage --replicas=3

# Auto-scaling based on CPU
kubectl autoscale deployment streamflow-analytics \
  --cpu-percent=70 --min=2 --max=10
```

### Performance Optimization
- **Connection pooling** for database connections
- **Redis caching** for frequently accessed data
- **Async processing** for non-blocking operations
- **Load balancing** across service replicas

## 🛠️ Development

### Project Structure
```
streamflow/
├── services/           # Backend microservices
│   ├── ingestion/     # Event ingestion service
│   ├── analytics/     # Analytics processing
│   ├── alerting/      # Alert management
│   ├── storage/       # Data storage service
│   └── dashboard/     # Dashboard API
├── web-ui/            # React frontend
├── shared/            # Shared utilities
├── terraform/         # AWS infrastructure
├── helm/              # Helm charts
├── k8s/               # Kubernetes manifests
├── tests/             # Test suites
└── docs/              # Documentation
```

### Contributing
1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

### Development Setup
```bash
# Setup development environment
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Install pre-commit hooks
pre-commit install

# Run development services
docker-compose up -d
```

## 📋 Requirements

### System Requirements
- **Python**: 3.8+
- **Node.js**: 16+
- **PostgreSQL**: 12+
- **Redis**: 6+
- **RabbitMQ**: 3.8+

### Kubernetes Requirements
- **Kubernetes**: 1.28+
- **Helm**: 3.0+ (for Helm deployment)
- **NGINX Ingress Controller**
- **cert-manager** (for TLS)

### AWS Requirements (Terraform)
- **EKS**: 1.28+
- **RDS**: PostgreSQL 15+
- **ElastiCache**: Redis 7+
- **VPC**: Multi-AZ setup

## 📚 Documentation

- [Deployment Guide](./DEPLOYMENT.md) - Comprehensive deployment instructions
- [API Documentation](./docs/API.md) - Complete API reference
- [Contributing Guide](./CONTRIBUTING.md) - Development guidelines
- [Getting Started](./GETTING_STARTED.md) - Quick start tutorial

## 🆘 Support

### Troubleshooting
Common issues and solutions:

1. **Services not starting**: Check logs with `kubectl logs -f deployment/streamflow-service`
2. **Database connection errors**: Verify connection strings and credentials
3. **UI not loading**: Check ingress configuration and DNS resolution
4. **Performance issues**: Monitor resource usage and scale accordingly

### Getting Help
- **Issues**: [GitHub Issues](https://github.com/your-org/streamflow/issues)
- **Discussions**: [GitHub Discussions](https://github.com/your-org/streamflow/discussions)
- **Documentation**: [Project Wiki](https://github.com/your-org/streamflow/wiki)

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- Built with [FastAPI](https://fastapi.tiangolo.com/) for high-performance APIs
- Frontend powered by [React](https://reactjs.org/) and [Tailwind CSS](https://tailwindcss.com/)
- Charts created with [Recharts](https://recharts.org/)
- Infrastructure managed with [Terraform](https://terraform.io/) and [Kubernetes](https://kubernetes.io/)
- Monitoring with [Prometheus](https://prometheus.io/) and [Grafana](https://grafana.com/)

---

**StreamFlow** - Real-time analytics platform for the modern enterprise 🌊
