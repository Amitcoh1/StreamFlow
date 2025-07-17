# StreamFlow Deployment Guide

This guide provides comprehensive instructions for deploying the StreamFlow real-time analytics pipeline in production.

## 🚀 Quick Start

### Prerequisites

- Docker & Docker Compose
- Python 3.8+
- Git
- Make (optional, for convenience commands)

### 1. Clone and Setup

```bash
git clone <repository-url>
cd streamflow
cp .env.example .env
# Edit .env with your configuration
```

### 2. Quick Development Setup

```bash
make quick-start
```

This will:
- Setup environment file
- Install dependencies
- Build Docker images
- Start infrastructure services
- Run database migrations
- Seed with sample data

### 3. Access the Application

- **Dashboard UI**: http://localhost:8004
- **API Documentation**: http://localhost:8004/docs
- **Grafana**: http://localhost:3000 (admin/admin)
- **RabbitMQ Management**: http://localhost:15672 (guest/guest)

## 🏗️ Architecture Overview

StreamFlow consists of 5 microservices:

1. **Dashboard Service** (Port 8004) - Web UI and main API
2. **Ingestion Service** (Port 8001) - Event collection and validation
3. **Analytics Service** (Port 8002) - Real-time stream processing
4. **Alerting Service** (Port 8003) - Rule evaluation and notifications
5. **Storage Service** (Port 8005) - Data persistence and retrieval

### Infrastructure Components

- **PostgreSQL** - Primary database
- **Redis** - Caching and session storage
- **RabbitMQ** - Message queue for event processing
- **Prometheus** - Metrics collection
- **Grafana** - Monitoring dashboards

## 🛠️ Development Setup

### 1. Local Development

```bash
# Install dependencies
make install

# Start infrastructure only
docker-compose up -d postgres redis rabbitmq

# Run services individually
make run-dashboard
# or
python -m services.dashboard.main
```

### 2. With Docker (Recommended)

```bash
# Start everything with Docker
make docker

# View logs
make logs

# Stop services
make stop
```

### 3. Environment Configuration

Key environment variables in `.env`:

```bash
# Database
DATABASE_URL=postgresql+asyncpg://streamflow:password@localhost:5432/streamflow

# Authentication
JWT_SECRET_KEY=your-super-secret-key-here

# External Services
REDIS_URL=redis://localhost:6379
RABBITMQ_URL=amqp://guest:guest@localhost:5672/

# UI Configuration
UI_TITLE=StreamFlow Dashboard
UI_THEME=dark
```

## 🧪 Testing

### Run All Tests

```bash
make test
```

### Test Categories

```bash
# Unit tests
make test-unit

# Integration tests
make test-integration

# Performance tests
make test-performance

# With coverage
make test-cov
```

### Code Quality

```bash
# Linting
make lint

# Format code
make format

# Security scan
make security-scan
```

## 📊 Features

### Real-time Dashboard

- Live event monitoring
- Interactive charts and graphs
- System health indicators
- Alert management interface

### Event Processing

- High-throughput event ingestion
- Real-time stream analytics
- Configurable processing rules
- Batch and streaming modes

### Alerting System

- Rule-based alert conditions
- Multiple notification channels (Email, Slack, Webhooks)
- Alert suppression and escalation
- Customizable templates

### Monitoring & Observability

- Prometheus metrics
- Structured logging
- Health checks
- Performance monitoring

## 🔒 Security Features

- JWT-based authentication
- Role-based access control (RBAC)
- Input validation and sanitization
- Rate limiting
- SQL injection prevention
- XSS protection

## 🚀 Production Deployment

### 1. Environment Preparation

```bash
# Production environment file
cp .env.example .env.production

# Update production settings
ENVIRONMENT=production
DEBUG=false
JWT_SECRET_KEY=<strong-production-key>
DATABASE_URL=postgresql+asyncpg://user:pass@prod-db:5432/streamflow
```

### 2. Docker Production Deployment

```bash
# Build production images
docker-compose -f docker-compose.prod.yml build

# Deploy
docker-compose -f docker-compose.prod.yml up -d

# Run migrations
docker-compose -f docker-compose.prod.yml exec dashboard alembic upgrade head
```

### 3. Kubernetes Deployment

```bash
# Apply Kubernetes manifests
kubectl apply -f k8s/

# Scale services
kubectl scale deployment analytics --replicas=3
```

### 4. Health Checks

```bash
# Check all services
make health

# Individual service health
curl http://localhost:8004/health
```

## 📈 Scaling

### Horizontal Scaling

```bash
# Scale analytics service
docker-compose up -d --scale analytics=3

# Scale with Kubernetes
kubectl scale deployment analytics --replicas=5
```

### Performance Tuning

Key configuration parameters:

```bash
# Processing
BATCH_SIZE=1000
PROCESSING_TIMEOUT=30
MAX_RETRIES=3

# Database
DATABASE_POOL_SIZE=10
DATABASE_MAX_OVERFLOW=20

# Monitoring
METRICS_ENABLED=true
HEALTH_CHECK_INTERVAL=30
```

## 🔧 Maintenance

### Database Operations

```bash
# Create migration
make migrate-create

# Run migrations
make migrate

# Backup database
make backup-db

# Restore database
make restore-db
```

### Monitoring

```bash
# View metrics
make metrics

# Check logs
make logs

# Service-specific logs
make logs-service
```

### Updates

```bash
# Pull latest changes
git pull origin main

# Rebuild and restart
make build
make docker
```

## 🐛 Troubleshooting

### Common Issues

1. **Database Connection Issues**
   ```bash
   # Check database status
   docker-compose ps postgres
   
   # View database logs
   docker-compose logs postgres
   ```

2. **Message Queue Problems**
   ```bash
   # Check RabbitMQ status
   curl http://localhost:15672/api/overview
   
   # Restart RabbitMQ
   docker-compose restart rabbitmq
   ```

3. **High Memory Usage**
   ```bash
   # Monitor resource usage
   docker stats
   
   # Adjust batch sizes in .env
   BATCH_SIZE=500
   ```

### Debug Mode

```bash
# Enable debug logging
echo "DEBUG=true" >> .env
echo "LOG_LEVEL=DEBUG" >> .env

# Restart services
make stop && make docker
```

## 📋 Maintenance Tasks

### Daily
- Monitor system health
- Check error logs
- Verify backup completion

### Weekly
- Review performance metrics
- Update dependencies
- Security scans

### Monthly
- Database maintenance
- Log rotation
- Capacity planning

## 🔐 Security Considerations

### Production Security Checklist

- [ ] Change default passwords
- [ ] Use strong JWT secret keys
- [ ] Enable HTTPS/TLS
- [ ] Configure firewall rules
- [ ] Set up monitoring alerts
- [ ] Regular security updates
- [ ] Backup encryption
- [ ] Access logging

### Environment Variables Security

Never commit sensitive values to version control:

```bash
# Use secrets management
JWT_SECRET_KEY=${JWT_SECRET}
DATABASE_PASSWORD=${DB_PASSWORD}
SMTP_PASSWORD=${SMTP_SECRET}
```

## 📞 Support

For issues and questions:

- GitHub Issues: [Repository Issues](https://github.com/AmitCoh1/streamFlow/issues)
- Email: amitcoh1@gmail.com
- Documentation: [StreamFlow Docs](./docs/)

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.