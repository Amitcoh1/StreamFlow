# StreamFlow 🌊

A real-time analytics pipeline built with Python, FastAPI, and RabbitMQ.

**Developed by Amit Cohen**

## 🚀 Features

### Core Capabilities
- **Real-time Event Processing**: Handle millions of events per second
- **Microservices Architecture**: Scalable, loosely-coupled services
- **Multiple Data Sources**: REST APIs, WebSockets, message queues
- **Advanced Analytics**: Stream processing with windowing and aggregations
- **Intelligent Alerting**: Rule-based alerts with multiple notification channels
- **Real-time Dashboards**: Live metrics and historical data visualization

### Production Ready
- **High Availability**: Circuit breakers, retries, and graceful degradation
- **Observability**: Prometheus metrics, structured logging, distributed tracing
- **Security**: JWT authentication, input validation, rate limiting
- **Scalability**: Horizontal scaling with automatic load balancing
- **Docker Support**: Multi-stage builds with production optimizations

## 🏗️ Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│  Event Sources  │───▶│  Ingestion API  │───▶│   RabbitMQ      │
│  (REST/WS)      │    │   (FastAPI)     │    │  Topic Exchange │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                                        │
                        ┌─────────────────┐            │
                        │   Analytics     │◀───────────┘
                        │   Pipeline      │
                        └─────────────────┘
                                 │
                     ┌───────────┼───────────┐
                     ▼           ▼           ▼
            ┌─────────────┐ ┌─────────┐ ┌─────────────┐
            │Alert Engine │ │Dashboard│ │Data Storage │
            │   Service   │ │   API   │ │   Service   │
            └─────────────┘ └─────────┘ └─────────────┘
```

## 🛠️ Services

### 1. Event Ingestion Service
- **REST API** for event collection
- **WebSocket** support for real-time streams
- **Rate limiting** and input validation
- **Health checks** and monitoring

### 2. Analytics Pipeline Service
- **Stream processing** with configurable windows
- **Real-time aggregations** and transformations
- **Custom rule engine** for complex analytics
- **Batch and stream processing** modes

### 3. Alert Engine Service
- **Rule-based alerting** with custom conditions
- **Multiple channels**: Email, Slack, webhooks
- **Alert suppression** and escalation
- **Notification templates** and customization

### 4. Dashboard API Service
- **Real-time metrics** via WebSocket
- **Historical data** queries
- **Authentication** and authorization
- **RESTful API** for dashboard integration

### 5. Data Storage Service
- **Time-series optimization** for metrics
- **Automated retention** policies
- **Backup and recovery** procedures
- **Multi-tier storage** strategy

## 🚦 Quick Start

### Prerequisites
- Python 3.8+
- Docker & Docker Compose
- RabbitMQ
- PostgreSQL
- Redis

### Installation

```bash
# Clone the repository
git clone https://github.com/streamflow/streamflow.git
cd streamflow

# Install dependencies
pip install -r requirements.txt

# Install in development mode
pip install -e .

# Start infrastructure
docker-compose up -d rabbitmq postgres redis

# Run database migrations
alembic upgrade head

# Start services
streamflow start --all
```

### Basic Usage

```python
from streamflow import StreamFlow
from streamflow.models import Event

# Initialize StreamFlow
sf = StreamFlow()

# Send an event
event = Event(
    type="user.click",
    data={"user_id": "123", "page": "/dashboard"},
    timestamp=datetime.utcnow()
)

await sf.ingestion.send_event(event)

# Set up an alert
alert_rule = {
    "name": "High Error Rate",
    "condition": "error_rate > 0.05",
    "window": "5m",
    "channels": ["email", "slack"]
}

await sf.alerting.create_rule(alert_rule)
```

## 🔧 Configuration

### Environment Variables

```bash
# RabbitMQ Configuration
RABBITMQ_URL=amqp://guest:guest@localhost:5672/
RABBITMQ_EXCHANGE_EVENTS=events
RABBITMQ_EXCHANGE_ANALYTICS=analytics

# Database Configuration
DATABASE_URL=postgresql+asyncpg://user:pass@localhost/streamflow
REDIS_URL=redis://localhost:6379

# Service Configuration
INGESTION_PORT=8001
ANALYTICS_PORT=8002
ALERTING_PORT=8003
DASHBOARD_PORT=8004
STORAGE_PORT=8005

# Security
JWT_SECRET_KEY=your-secret-key-here
JWT_ALGORITHM=HS256
JWT_EXPIRE_MINUTES=30
```

### Docker Compose

```yaml
version: '3.8'

services:
  ingestion:
    build: ./services/ingestion
    ports:
      - "8001:8000"
    environment:
      - RABBITMQ_URL=amqp://rabbitmq:5672
    depends_on:
      - rabbitmq
      - postgres

  analytics:
    build: ./services/analytics
    environment:
      - RABBITMQ_URL=amqp://rabbitmq:5672
    depends_on:
      - rabbitmq
      - postgres

  # ... other services
```

## 📊 Monitoring

### Metrics
- **Event throughput**: Events/second processed
- **Processing latency**: End-to-end processing time
- **Queue depth**: RabbitMQ queue metrics
- **Error rates**: Failed processing percentage
- **Resource usage**: CPU, memory, disk utilization

### Health Checks
- `/health` - Service health status
- `/ready` - Service readiness check
- `/metrics` - Prometheus metrics endpoint

### Dashboards
- **Grafana** dashboards for operational metrics
- **Real-time** event monitoring
- **Alert history** and performance tracking

## 🧪 Testing

```bash
# Run unit tests
pytest tests/unit/

# Run integration tests
pytest tests/integration/

# Run with coverage
pytest --cov=streamflow tests/

# Run performance tests
pytest tests/performance/
```

## 🚀 Deployment

### Docker
```bash
# Build images
docker-compose build

# Deploy to production
docker-compose -f docker-compose.prod.yml up -d
```

### Kubernetes
```bash
# Deploy with Helm
helm install streamflow ./helm/streamflow

# Scale services
kubectl scale deployment analytics --replicas=3
```

## 🤝 Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🔗 Links

- [Documentation](https://streamflow.readthedocs.io)
- [API Reference](https://api.streamflow.dev)
- [Examples](./examples/)
- [Contributing Guide](./CONTRIBUTING.md)

## 📞 Support

- [GitHub Issues](https://github.com/amitcohen/streamflow/issues)
- [Discord Community](https://discord.gg/streamflow)
- [Email Support](mailto:amit.cohen@streamflow.dev)

---

**Created by Amit Cohen** - [GitHub](https://github.com/amitcohen) | [LinkedIn](https://linkedin.com/in/amitcohen) | [Email](mailto:amit.cohen@streamflow.dev)
