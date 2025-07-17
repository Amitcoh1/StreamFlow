# StreamFlow: Getting Started Guide

## 🚀 How to Use StreamFlow Analytics System

StreamFlow is a real-time analytics pipeline that helps organizations process millions of events per second and gain real-time insights from their data streams.

## 🎯 What StreamFlow Does for Your Users

### 1. **Real-Time Analytics**
- Process user interactions, system events, and business metrics in real-time
- Detect patterns and anomalies as they happen
- Generate actionable insights instantly

### 2. **Intelligent Alerting**
- Automatic notifications when thresholds are exceeded
- Custom rule-based alerts for business logic
- Multi-channel notifications (email, Slack, webhooks)

### 3. **Scalable Data Processing**
- Handle millions of events per second
- Auto-scaling based on load
- Fault-tolerant with automatic recovery

### 4. **Integration-Ready**
- REST APIs for easy integration
- WebSocket support for real-time streams
- Standard protocols and formats

## 📋 Prerequisites

Before starting, ensure you have:
- Python 3.8+
- Docker & Docker Compose
- Git

## 🛠️ Installation & Setup

### Step 1: Clone and Setup
```bash
# Clone the repository
git clone https://github.com/amitcohen/streamflow.git
cd streamflow

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
pip install -e .
```

### Step 2: Start Infrastructure
```bash
# Start RabbitMQ, PostgreSQL, and Redis
docker-compose up -d rabbitmq postgres redis

# Wait for services to be ready (check logs)
docker-compose logs -f
```

### Step 3: Initialize Database
```bash
# Run database migrations
alembic upgrade head
```

### Step 4: Start StreamFlow Services
```bash
# Start all services
docker-compose up -d

# Or start individual services
docker-compose up -d ingestion analytics alerting dashboard storage
```

## 🔧 Configuration

### Environment Variables
Create a `.env` file in your project root:

```env
# RabbitMQ Configuration
RABBITMQ_URL=amqp://admin:admin123@localhost:5672/
RABBITMQ_EXCHANGE_EVENTS=events
RABBITMQ_EXCHANGE_ANALYTICS=analytics

# Database Configuration
DATABASE_URL=postgresql+asyncpg://streamflow:streamflow123@localhost/streamflow
REDIS_URL=redis://localhost:6379

# Service Ports
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

## 📊 How to Integrate with Your Existing System

### 1. **Send Events via REST API**
```python
import requests
import json
from datetime import datetime

# Send a user click event
event_data = {
    "type": "user.click",
    "source": "web_app",
    "data": {
        "user_id": "user123",
        "page": "/dashboard",
        "element": "button.submit"
    },
    "timestamp": datetime.utcnow().isoformat(),
    "severity": "low",
    "tags": ["frontend", "user-interaction"]
}

response = requests.post(
    "http://localhost:8001/events",
    json=event_data,
    headers={"Content-Type": "application/json"}
)
```

### 2. **Real-Time Streaming via WebSocket**
```python
import asyncio
import websockets
import json

async def stream_events():
    uri = "ws://localhost:8001/events/stream"
    async with websockets.connect(uri) as websocket:
        # Send real-time events
        event = {
            "type": "system.metric",
            "source": "monitoring",
            "data": {"cpu_usage": 75.5, "memory_usage": 60.2},
            "timestamp": datetime.utcnow().isoformat()
        }
        await websocket.send(json.dumps(event))
        
        # Receive processed results
        response = await websocket.recv()
        print(f"Processed: {response}")

asyncio.run(stream_events())
```

### 3. **Set Up Custom Alerts**
```python
import requests

# Create an alert rule
alert_rule = {
    "name": "High CPU Usage",
    "condition": "data.cpu_usage > 80",
    "window_seconds": 300,  # 5 minutes
    "channels": ["email", "slack"],
    "template": "CPU usage is {{ data.cpu_usage }}% on {{ source }}",
    "recipients": ["ops-team@company.com"]
}

response = requests.post(
    "http://localhost:8003/alerts/rules",
    json=alert_rule
)
```

### 4. **Query Analytics Data**
```python
import requests

# Get real-time metrics
response = requests.get("http://localhost:8004/metrics/realtime")
metrics = response.json()

# Get historical data
response = requests.get(
    "http://localhost:8004/metrics/history",
    params={
        "start": "2025-01-01T00:00:00Z",
        "end": "2025-01-02T00:00:00Z",
        "metric": "user.clicks"
    }
)
historical_data = response.json()
```

## 🎯 Common Use Cases

### 1. **E-commerce Analytics**
```python
# Track user behavior
user_events = [
    {"type": "user.page_view", "data": {"page": "/product/123"}},
    {"type": "user.add_to_cart", "data": {"product_id": "123", "quantity": 2}},
    {"type": "user.purchase", "data": {"order_id": "order456", "total": 99.99}}
]

# Set up conversion tracking
conversion_rule = {
    "name": "Conversion Rate Alert",
    "condition": "conversion_rate < 0.02",  # Less than 2%
    "window_seconds": 3600,  # 1 hour
    "channels": ["email"]
}
```

### 2. **System Monitoring**
```python
# Monitor system health
system_events = [
    {"type": "system.cpu", "data": {"usage": 85.2}},
    {"type": "system.memory", "data": {"usage": 92.1}},
    {"type": "system.disk", "data": {"usage": 78.5}}
]

# Alert on high resource usage
resource_alert = {
    "name": "High Resource Usage",
    "condition": "data.usage > 90",
    "channels": ["slack", "pagerduty"]
}
```

### 3. **IoT Data Processing**
```python
# Process sensor data
sensor_events = [
    {"type": "sensor.temperature", "data": {"value": 25.5, "unit": "celsius"}},
    {"type": "sensor.humidity", "data": {"value": 60.2, "unit": "percent"}},
    {"type": "sensor.pressure", "data": {"value": 1013.25, "unit": "hPa"}}
]

# Detect anomalies
anomaly_rule = {
    "name": "Temperature Anomaly",
    "condition": "data.value > 30 or data.value < 10",
    "channels": ["webhook"]
}
```

## 📈 Monitoring & Dashboards

### Health Checks
```bash
# Check service health
curl http://localhost:8001/health  # Ingestion service
curl http://localhost:8002/health  # Analytics service
curl http://localhost:8003/health  # Alerting service
curl http://localhost:8004/health  # Dashboard service
curl http://localhost:8005/health  # Storage service
```

### Metrics Endpoint
```bash
# Get Prometheus metrics
curl http://localhost:8001/metrics
```

### Dashboard Access
- **RabbitMQ Management**: http://localhost:15672 (admin/admin123)
- **Dashboard API**: http://localhost:8004
- **Real-time Metrics**: ws://localhost:8004/metrics/live

## 🔧 Advanced Configuration

### Custom Analytics Rules
```python
from streamflow.services.analytics import StreamProcessor

processor = StreamProcessor()

# Register custom window
processor.register_window("5min", 300)  # 5 minutes

# Register custom aggregator
def calculate_avg_response_time(events):
    response_times = [e.data.get("response_time", 0) for e in events]
    return sum(response_times) / len(response_times) if response_times else 0

processor.register_aggregator("avg_response_time", calculate_avg_response_time)

# Register custom rule
async def high_latency_action(event):
    if event.data.get("response_time", 0) > 1000:  # > 1 second
        return {"alert": "High latency detected", "value": event.data["response_time"]}
    return None

processor.register_rule("high_latency", "data.response_time > 1000", high_latency_action)
```

## 🐛 Troubleshooting

### Common Issues

1. **Services won't start**
   ```bash
   # Check logs
   docker-compose logs -f
   
   # Restart services
   docker-compose restart
   ```

2. **Database connection issues**
   ```bash
   # Check PostgreSQL is running
   docker-compose ps postgres
   
   # Reset database
   docker-compose down -v
   docker-compose up -d postgres
   ```

3. **RabbitMQ connection problems**
   ```bash
   # Check RabbitMQ status
   docker-compose exec rabbitmq rabbitmqctl status
   
   # Reset RabbitMQ
   docker-compose restart rabbitmq
   ```

## 📚 Next Steps

1. **Explore Examples**: Check the `/examples` directory for more use cases
2. **Read Documentation**: Visit the `/docs` directory for detailed API reference
3. **Join Community**: Get support and share experiences
4. **Contribute**: Help improve StreamFlow for everyone

## 🤝 Integration Benefits for Your Users

### For Developers
- **Easy Integration**: Simple REST APIs and WebSocket support
- **Flexible**: Support for custom analytics rules and alerts
- **Scalable**: Handles millions of events per second
- **Reliable**: Built-in fault tolerance and monitoring

### For Business Users
- **Real-time Insights**: Instant visibility into business metrics
- **Proactive Alerts**: Get notified before issues become problems
- **Data-Driven Decisions**: Rich analytics and historical data
- **Cost Effective**: Open-source with enterprise features

### For Operations Teams
- **Observability**: Comprehensive monitoring and logging
- **Scalability**: Auto-scaling based on demand
- **Reliability**: High availability with automatic failover
- **Security**: JWT authentication and input validation

---

**Get Started Today!** 🚀

StreamFlow makes it easy to add real-time analytics to your existing systems. Start with sending a simple event and gradually add more sophisticated analytics and alerting rules as your needs grow.

For questions and support, contact: amit.cohen@streamflow.dev
