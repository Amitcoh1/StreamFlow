# StreamFlow API Documentation

## Overview

StreamFlow is a real-time analytics pipeline built with Python, FastAPI, and RabbitMQ. It provides a complete microservices architecture for event processing, analytics, alerting, and real-time dashboards.

## Architecture

### Core Components

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│  Event Sources  │───▶│  Ingestion API  │───▶│   RabbitMQ      │
│  (REST/WS)      │    │   (FastAPI)     │    │  Topic Exchange │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                                        │
                        ┌─────────────────┐             │
                        │   Analytics     │◀───────────-┘
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

## API Reference

### Event Ingestion Service

Base URL: `http://localhost:8001`

#### Health Check

```http
GET /health
```

**Response:**
```json
{
  "status": "healthy",
  "service": "ingestion",
  "version": "0.1.0",
  "timestamp": "2023-12-01T12:00:00Z",
  "checks": {
    "database": {"status": "healthy"},
    "message_broker": {"status": "healthy"},
    "websocket_connections": 5
  }
}
```

#### Create Event

```http
POST /events
Authorization: Bearer <token>
Content-Type: application/json
```

**Request Body:**
```json
{
  "type": "web.click",
  "source": "website",
  "data": {
    "page": "/dashboard",
    "user_id": "123",
    "element": "button.submit"
  },
  "severity": "medium",
  "correlation_id": "optional-correlation-id",
  "session_id": "optional-session-id",
  "user_id": "user123",
  "tags": ["frontend", "user-interaction"]
}
```

**Response:**
```json
{
  "success": true,
  "message": "Event created successfully",
  "data": {
    "event_id": "550e8400-e29b-41d4-a716-446655440000"
  },
  "timestamp": "2023-12-01T12:00:00Z"
}
```

#### Create Batch Events

```http
POST /events/batch
Authorization: Bearer <token>
Content-Type: application/json
```

**Request Body:**
```json
{
  "events": [
    {
      "type": "web.click",
      "source": "website",
      "data": {"page": "/dashboard"},
      "severity": "medium"
    },
    {
      "type": "api.request",
      "source": "api-gateway",
      "data": {"endpoint": "/api/users", "method": "GET"},
      "severity": "low"
    }
  ]
}
```

**Response:**
```json
{
  "success": true,
  "message": "Batch of 2 events created successfully",
  "data": {
    "event_ids": [
      "550e8400-e29b-41d4-a716-446655440000",
      "550e8400-e29b-41d4-a716-446655440001"
    ]
  }
}
```

#### Get Event

```http
GET /events/{event_id}
Authorization: Bearer <token>
```

**Response:**
```json
{
  "success": true,
  "message": "Event retrieved successfully",
  "data": {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "type": "web.click",
    "source": "website",
    "timestamp": "2023-12-01T12:00:00Z",
    "data": {"page": "/dashboard"},
    "severity": "medium",
    "tags": ["frontend"]
  }
}
```

#### WebSocket Connection

```javascript
const ws = new WebSocket('ws://localhost:8001/ws');

// Send event via WebSocket
ws.send(JSON.stringify({
  type: 'event',
  data: {
    event_type: 'user.activity',
    user_id: 'user123',
    action: 'page_view',
    page: '/dashboard'
  }
}));

// Receive acknowledgment
ws.onmessage = function(event) {
  console.log('Received:', event.data);
};
```

### Dashboard API Service

Base URL: `http://localhost:8004`

#### Get Real-time Metrics

```http
GET /metrics/realtime
Authorization: Bearer <token>
```

**Response:**
```json
{
  "metrics": {
    "events_per_second": 150.5,
    "active_users": 1247,
    "error_rate": 0.02,
    "response_time_avg": 0.234
  },
  "timestamp": "2023-12-01T12:00:00Z"
}
```

#### Get Historical Data

```http
GET /metrics/historical?start=2023-12-01T00:00:00Z&end=2023-12-01T23:59:59Z&interval=1h
Authorization: Bearer <token>
```

**Response:**
```json
{
  "data": [
    {
      "timestamp": "2023-12-01T00:00:00Z",
      "events_total": 15420,
      "unique_users": 1247,
      "error_count": 23
    },
    {
      "timestamp": "2023-12-01T01:00:00Z",
      "events_total": 16890,
      "unique_users": 1456,
      "error_count": 18
    }
  ],
  "pagination": {
    "page": 1,
    "total": 24,
    "has_next": true
  }
}
```

#### WebSocket Live Updates

```javascript
const ws = new WebSocket('ws://localhost:8004/ws/metrics');

ws.onmessage = function(event) {
  const data = JSON.parse(event.data);
  console.log('Live metrics:', data);
};
```

### Storage API Service

Base URL: `http://localhost:8005`

#### Query Events

```http
GET /events?start=2023-12-01T00:00:00Z&end=2023-12-01T23:59:59Z&type=web.click&page=1&limit=100
Authorization: Bearer <token>
```

**Response:**
```json
{
  "data": [
    {
      "id": "550e8400-e29b-41d4-a716-446655440000",
      "type": "web.click",
      "source": "website",
      "timestamp": "2023-12-01T12:00:00Z",
      "data": {"page": "/dashboard"},
      "severity": "medium"
    }
  ],
  "pagination": {
    "page": 1,
    "page_size": 100,
    "total": 15420,
    "pages": 155,
    "has_next": true,
    "has_prev": false
  }
}
```

#### Get Event Aggregations

```http
GET /events/aggregations?metric=count&group_by=type&start=2023-12-01T00:00:00Z&end=2023-12-01T23:59:59Z
Authorization: Bearer <token>
```

**Response:**
```json
{
  "aggregations": {
    "web.click": 8542,
    "api.request": 4231,
    "user.login": 1247,
    "error": 89
  },
  "total": 14109,
  "period": {
    "start": "2023-12-01T00:00:00Z",
    "end": "2023-12-01T23:59:59Z"
  }
}
```

## Data Models

### Event Model

```python
class Event(BaseModel):
    id: UUID
    type: EventType  # Enum: web.click, api.request, user.login, etc.
    source: str
    timestamp: datetime
    severity: EventSeverity  # Enum: low, medium, high, critical
    data: Dict[str, Any]
    metadata: Dict[str, Any]
    correlation_id: Optional[str]
    session_id: Optional[str]
    user_id: Optional[str]
    tags: List[str]
```

### Alert Rule Model

```python
class AlertRule(BaseModel):
    id: UUID
    name: str
    description: Optional[str]
    condition: str  # Expression like "error_rate > 0.05"
    threshold: float
    window: str  # Time window like "5m", "1h"
    level: AlertLevel  # Enum: info, warning, error, critical
    channels: List[AlertChannel]  # Enum: email, slack, webhook, sms
    enabled: bool
    suppression_minutes: int
    escalation_minutes: int
    tags: List[str]
    metadata: Dict[str, Any]
```

### Metric Data Model

```python
class MetricData(BaseModel):
    name: str
    type: MetricType  # Enum: counter, gauge, histogram, timer
    value: float
    timestamp: datetime
    tags: Dict[str, str]
    metadata: Dict[str, Any]
```

## Configuration

### Environment Variables

```bash
# Application
ENVIRONMENT=production
DEBUG=false
APP_NAME=StreamFlow
APP_VERSION=0.1.0

# Database
DATABASE_URL=postgresql+asyncpg://user:pass@localhost/streamflow
DATABASE_POOL_SIZE=20
DATABASE_MAX_OVERFLOW=30

# RabbitMQ
RABBITMQ_URL=amqp://user:pass@localhost:5672/
RABBITMQ_EXCHANGE_EVENTS=events
RABBITMQ_EXCHANGE_ANALYTICS=analytics
RABBITMQ_EXCHANGE_ALERTS=alerts

# Redis
REDIS_URL=redis://localhost:6379/0
REDIS_MAX_CONNECTIONS=50

# Security
JWT_SECRET_KEY=your-secret-key-here
JWT_ALGORITHM=HS256
JWT_EXPIRE_MINUTES=30

# Services
INGESTION_PORT=8001
ANALYTICS_PORT=8002
ALERTING_PORT=8003
DASHBOARD_PORT=8004
STORAGE_PORT=8005

# Monitoring
PROMETHEUS_ENABLED=true
JAEGER_ENABLED=true
LOG_LEVEL=INFO
LOG_FORMAT=json

# Rate Limiting
RATE_LIMIT_ENABLED=true
RATE_LIMIT_REQUESTS_PER_MINUTE=100
RATE_LIMIT_BURST_SIZE=10
```

### Configuration File (config.yaml)

```yaml
# StreamFlow Configuration
app:
  name: StreamFlow
  version: 0.1.0
  environment: production
  debug: false

database:
  url: postgresql+asyncpg://user:pass@localhost/streamflow
  pool_size: 20
  max_overflow: 30
  echo: false

rabbitmq:
  url: amqp://user:pass@localhost:5672/
  exchanges:
    events: events
    analytics: analytics
    alerts: alerts
  max_connections: 10
  heartbeat: 600

redis:
  url: redis://localhost:6379/0
  max_connections: 50

security:
  jwt:
    secret_key: your-secret-key-here
    algorithm: HS256
    expire_minutes: 30
  bcrypt_rounds: 12

monitoring:
  prometheus:
    enabled: true
    port: 8080
  jaeger:
    enabled: true
    endpoint: http://jaeger:14268/api/traces
  logging:
    level: INFO
    format: json

rate_limiting:
  enabled: true
  requests_per_minute: 100
  burst_size: 10
```

## Error Handling

### Standard Error Response

```json
{
  "error": "ValidationError",
  "message": "Invalid event type provided",
  "details": {
    "field": "type",
    "allowed_values": ["web.click", "api.request", "user.login", "error"]
  },
  "timestamp": "2023-12-01T12:00:00Z",
  "correlation_id": "550e8400-e29b-41d4-a716-446655440000"
}
```

### HTTP Status Codes

- `200 OK` - Request successful
- `201 Created` - Resource created successfully
- `400 Bad Request` - Invalid request data
- `401 Unauthorized` - Authentication required
- `403 Forbidden` - Insufficient permissions
- `404 Not Found` - Resource not found
- `422 Unprocessable Entity` - Validation error
- `429 Too Many Requests` - Rate limit exceeded
- `500 Internal Server Error` - Server error
- `502 Bad Gateway` - Service unavailable
- `503 Service Unavailable` - Service temporarily unavailable

## Authentication

### JWT Token Authentication

```http
POST /auth/login
Content-Type: application/json

{
  "username": "user@example.com",
  "password": "secure_password"
}
```

**Response:**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "expires_in": 1800
}
```

### Using Token in Requests

```http
GET /events
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

## Rate Limiting

### Default Limits

- **Events API**: 100 requests per minute per IP
- **Dashboard API**: 200 requests per minute per user
- **WebSocket**: 10 connections per IP

### Rate Limit Headers

```http
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 95
X-RateLimit-Reset: 1638360000
```

### Rate Limit Exceeded Response

```json
{
  "error": "RateLimitExceeded",
  "message": "Rate limit exceeded. Try again in 60 seconds.",
  "retry_after": 60,
  "limit": 100,
  "remaining": 0
}
```

## Monitoring and Observability

### Prometheus Metrics

Available at: `http://localhost:8080/metrics`

#### Key Metrics

- `streamflow_events_total` - Total events processed
- `streamflow_events_duration_seconds` - Event processing time
- `streamflow_active_connections` - Active WebSocket connections
- `streamflow_queue_depth` - RabbitMQ queue depth
- `streamflow_alerts_fired_total` - Total alerts fired
- `streamflow_http_requests_total` - HTTP requests by endpoint
- `streamflow_http_request_duration_seconds` - HTTP request duration

### Health Check Endpoints

- `/health` - Service health status
- `/ready` - Service readiness check
- `/metrics` - Prometheus metrics

### Logging

#### Log Format (JSON)

```json
{
  "timestamp": "2023-12-01T12:00:00Z",
  "level": "INFO",
  "service": "ingestion",
  "message": "Event processed successfully",
  "correlation_id": "550e8400-e29b-41d4-a716-446655440000",
  "event_id": "550e8400-e29b-41d4-a716-446655440001",
  "user_id": "user123",
  "duration": 0.045,
  "extra": {
    "event_type": "web.click",
    "source": "website"
  }
}
```

#### Log Levels

- `DEBUG` - Detailed debug information
- `INFO` - General information
- `WARNING` - Warning messages
- `ERROR` - Error messages
- `CRITICAL` - Critical errors

## Deployment

### Docker Compose

```yaml
version: '3.8'

services:
  ingestion:
    image: streamflow/ingestion:latest
    ports:
      - "8001:8000"
    environment:
      - RABBITMQ_URL=amqp://rabbitmq:5672
      - DATABASE_URL=postgresql+asyncpg://postgres:5432/streamflow
    depends_on:
      - rabbitmq
      - postgres
```

### Kubernetes

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: streamflow-ingestion
spec:
  replicas: 3
  selector:
    matchLabels:
      app: streamflow-ingestion
  template:
    metadata:
      labels:
        app: streamflow-ingestion
    spec:
      containers:
      - name: ingestion
        image: streamflow/ingestion:latest
        ports:
        - containerPort: 8000
        env:
        - name: RABBITMQ_URL
          value: "amqp://rabbitmq:5672"
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: streamflow-secrets
              key: database-url
```

### Helm Chart

```bash
# Add Helm repository
helm repo add streamflow https://helm.streamflow.dev

# Install StreamFlow
helm install streamflow streamflow/streamflow \
  --set ingestion.replicas=3 \
  --set database.url=postgresql://... \
  --set rabbitmq.url=amqp://...
```

## Performance Tuning

### Database Optimization

```sql
-- Index optimization
CREATE INDEX CONCURRENTLY idx_events_timestamp ON events (timestamp);
CREATE INDEX CONCURRENTLY idx_events_type ON events (type);
CREATE INDEX CONCURRENTLY idx_events_source ON events (source);
CREATE INDEX CONCURRENTLY idx_events_user_id ON events (user_id);

-- Partitioning (PostgreSQL)
CREATE TABLE events_2023_12 PARTITION OF events
FOR VALUES FROM ('2023-12-01') TO ('2024-01-01');
```

### RabbitMQ Optimization

```python
# Connection pooling
RABBITMQ_MAX_CONNECTIONS = 20
RABBITMQ_HEARTBEAT = 600

# Queue configuration
queue_arguments = {
    'x-max-length': 100000,
    'x-message-ttl': 86400000,  # 24 hours
    'x-dead-letter-exchange': 'events.dlx'
}
```

### Application Optimization

```python
# Async configuration
import asyncio
asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

# Connection pooling
DATABASE_POOL_SIZE = 20
DATABASE_MAX_OVERFLOW = 30
REDIS_MAX_CONNECTIONS = 50

# Serialization optimization
import orjson
json_dumps = orjson.dumps
json_loads = orjson.loads
```

## Security Best Practices

### Authentication & Authorization

1. **JWT Tokens**: Use short-lived tokens (15-30 minutes)
2. **Refresh Tokens**: Implement refresh token rotation
3. **Role-Based Access**: Implement proper RBAC
4. **API Keys**: Use API keys for service-to-service communication

### Input Validation

```python
from pydantic import BaseModel, validator

class EventRequest(BaseModel):
    type: str
    source: str
    data: Dict[str, Any]
    
    @validator('type')
    def validate_type(cls, v):
        allowed_types = ['web.click', 'api.request', 'user.login']
        if v not in allowed_types:
            raise ValueError(f'Invalid event type: {v}')
        return v
```

### Rate Limiting

```python
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)

@app.post("/events")
@limiter.limit("100/minute")
async def create_event(request: Request, event: EventRequest):
    # Process event
    pass
```

### CORS Configuration

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://dashboard.example.com"],
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)
```

## Troubleshooting

### Common Issues

#### Connection Refused

```bash
# Check service status
curl -f http://localhost:8001/health

# Check Docker containers
docker-compose ps

# Check logs
docker-compose logs ingestion
```

#### High Memory Usage

```bash
# Check memory usage
docker stats

# Monitor Python memory
import psutil
process = psutil.Process()
print(f"Memory: {process.memory_info().rss / 1024 / 1024:.2f} MB")
```

#### Queue Backup

```bash
# Check RabbitMQ queue depth
rabbitmqctl list_queues name messages

# Purge queue if needed
rabbitmqctl purge_queue events.analytics
```

### Debug Mode

```python
# Enable debug logging
import logging
logging.basicConfig(level=logging.DEBUG)

# Enable SQL echo
DATABASE_ECHO = True

# Enable development mode
DEBUG = True
ENVIRONMENT = "development"
```

## Support

- **Documentation**: https://streamflow.readthedocs.io
- **GitHub Issues**: https://github.com/streamflow/streamflow/issues
- **Discord Community**: https://discord.gg/streamflow
- **Email Support**: support@streamflow.dev
