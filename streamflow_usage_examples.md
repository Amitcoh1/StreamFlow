# StreamFlow Usage Examples

## Installation and Setup

```bash
# Install the library
pip install streamflow

# Or for development
git clone https://github.com/streamflow/streamflow.git
cd streamflow
pip install -e .
```

## Basic Usage Examples

### 1. Simple Event Ingestion

```python
import asyncio
from datetime import datetime
from streamflow import StreamFlow
from streamflow.models import Event

async def basic_event_example():
    # Initialize StreamFlow
    sf = StreamFlow()
    
    # Create and send a simple event
    event = Event(
        type="user.click",
        data={"user_id": "123", "page": "/dashboard"},
        timestamp=datetime.utcnow()
    )
    
    # Send the event
    await sf.ingestion.send_event(event)
    print("Event sent successfully!")

# Run the example
asyncio.run(basic_event_example())
```

### 2. Batch Event Processing

```python
async def batch_events_example():
    sf = StreamFlow()
    
    # Create multiple events
    events = [
        Event(
            type="user.login",
            data={"user_id": f"user_{i}", "device": "mobile"},
            timestamp=datetime.utcnow()
        )
        for i in range(100)
    ]
    
    # Send events in batch
    await sf.ingestion.send_events_batch(events)
    print(f"Sent {len(events)} events in batch")

asyncio.run(batch_events_example())
```

## Advanced Analytics Examples

### 3. Setting Up Real-time Analytics

```python
from streamflow.analytics import AnalyticsRule, Window

async def analytics_setup_example():
    sf = StreamFlow()
    
    # Define analytics rules
    analytics_rules = [
        # Calculate click-through rate
        AnalyticsRule(
            name="ctr_calculation",
            input_events=["user.click", "user.impression"],
            window=Window(size="1m", type="tumbling"),
            aggregation="click_count / impression_count",
            output_event="metrics.ctr"
        ),
        
        # Track user session duration
        AnalyticsRule(
            name="session_duration",
            input_events=["user.login", "user.logout"],
            window=Window(size="session", type="session"),
            aggregation="max(timestamp) - min(timestamp)",
            output_event="metrics.session_duration"
        )
    ]
    
    # Register analytics rules
    for rule in analytics_rules:
        await sf.analytics.register_rule(rule)
    
    print("Analytics rules registered successfully!")

asyncio.run(analytics_setup_example())
```

### 4. Custom Stream Processing

```python
from streamflow.processors import StreamProcessor

class CustomEventProcessor(StreamProcessor):
    async def process(self, event):
        # Custom processing logic
        if event.type == "user.purchase":
            # Calculate commission
            commission = event.data.get("amount", 0) * 0.05
            
            # Create derived event
            commission_event = Event(
                type="business.commission",
                data={
                    "user_id": event.data["user_id"],
                    "commission": commission,
                    "original_amount": event.data["amount"]
                },
                timestamp=datetime.utcnow()
            )
            
            # Forward to next stage
            await self.emit(commission_event)

async def custom_processor_example():
    sf = StreamFlow()
    
    # Register custom processor
    processor = CustomEventProcessor()
    await sf.analytics.register_processor(processor)
    
    print("Custom processor registered!")

asyncio.run(custom_processor_example())
```

## Alerting Examples

### 5. Setting Up Alerts

```python
async def alerting_example():
    sf = StreamFlow()
    
    # Define alert rules
    alert_rules = [
        {
            "name": "High Error Rate",
            "condition": "error_rate > 0.05",
            "window": "5m",
            "channels": ["email", "slack"],
            "severity": "critical",
            "template": "Error rate is {{error_rate}}% in the last 5 minutes"
        },
        {
            "name": "Low Conversion Rate",
            "condition": "conversion_rate < 0.02",
            "window": "15m",
            "channels": ["email"],
            "severity": "warning",
            "cooldown": "30m"
        },
        {
            "name": "High Traffic Spike",
            "condition": "request_count > 1000",
            "window": "1m",
            "channels": ["webhook"],
            "severity": "info",
            "webhook_url": "https://your-service.com/alerts"
        }
    ]
    
    # Create alert rules
    for rule in alert_rules:
        await sf.alerting.create_rule(rule)
    
    print("Alert rules created successfully!")

asyncio.run(alerting_example())
```

### 6. Custom Alert Handlers

```python
from streamflow.alerting import AlertHandler

class CustomSlackHandler(AlertHandler):
    async def handle_alert(self, alert):
        # Custom Slack notification logic
        message = f"🚨 ALERT: {alert.rule_name}\n"
        message += f"Condition: {alert.condition}\n"
        message += f"Value: {alert.current_value}\n"
        message += f"Timestamp: {alert.timestamp}"
        
        # Send to Slack (implementation depends on your Slack setup)
        await self.send_slack_message(message)

async def custom_alert_handler_example():
    sf = StreamFlow()
    
    # Register custom alert handler
    handler = CustomSlackHandler()
    await sf.alerting.register_handler("custom_slack", handler)
    
    print("Custom alert handler registered!")

asyncio.run(custom_alert_handler_example())
```

## Dashboard and Visualization Examples

### 7. Real-time Dashboard Data

```python
async def dashboard_example():
    sf = StreamFlow()
    
    # Get real-time metrics
    metrics = await sf.dashboard.get_realtime_metrics([
        "user.active_sessions",
        "events.per_second",
        "system.cpu_usage",
        "alerts.active_count"
    ])
    
    print("Real-time metrics:", metrics)
    
    # Get historical data
    historical_data = await sf.dashboard.get_historical_data(
        metric="user.active_sessions",
        start_time=datetime.utcnow() - timedelta(hours=24),
        end_time=datetime.utcnow(),
        granularity="1h"
    )
    
    print("Historical data points:", len(historical_data))

asyncio.run(dashboard_example())
```

### 8. WebSocket Real-time Updates

```python
import websockets
import json

async def realtime_dashboard_example():
    # Connect to StreamFlow WebSocket
    uri = "ws://localhost:8004/ws/metrics"
    
    async with websockets.connect(uri) as websocket:
        # Subscribe to specific metrics
        subscription = {
            "action": "subscribe",
            "metrics": ["user.active_sessions", "events.per_second"]
        }
        await websocket.send(json.dumps(subscription))
        
        # Listen for real-time updates
        while True:
            data = await websocket.recv()
            metrics = json.loads(data)
            print(f"Real-time update: {metrics}")

# This would typically run in a web dashboard
# asyncio.run(realtime_dashboard_example())
```

## Configuration Examples

### 9. Production Configuration

```python
from streamflow import StreamFlow, Config

# Production configuration
config = Config(
    # RabbitMQ settings
    rabbitmq_url="amqp://prod-user:password@rabbitmq-cluster:5672/",
    rabbitmq_exchange_events="prod_events",
    
    # Database settings
    database_url="postgresql+asyncpg://user:pass@db-cluster/streamflow",
    redis_url="redis://redis-cluster:6379/0",
    
    # Service settings
    ingestion_port=8001,
    analytics_port=8002,
    alerting_port=8003,
    dashboard_port=8004,
    storage_port=8005,
    
    # Security settings
    jwt_secret_key="your-production-secret-key",
    jwt_expire_minutes=60,
    
    # Performance settings
    max_events_per_batch=1000,
    processing_timeout=30,
    queue_max_size=10000
)

async def production_setup():
    # Initialize with production config
    sf = StreamFlow(config=config)
    
    # Start all services
    await sf.start_all_services()
    print("StreamFlow started in production mode!")

# asyncio.run(production_setup())
```

### 10. Development and Testing

```python
async def development_example():
    # Development configuration with defaults
    sf = StreamFlow(environment="development")
    
    # Enable debug logging
    sf.set_log_level("DEBUG")
    
    # Send test events
    test_events = [
        Event(type="test.event", data={"test": True}),
        Event(type="user.click", data={"user_id": "test_user"}),
        Event(type="error.occurred", data={"error": "Test error"})
    ]
    
    for event in test_events:
        await sf.ingestion.send_event(event)
    
    # Wait for processing
    await asyncio.sleep(2)
    
    # Check results
    stats = await sf.get_processing_stats()
    print("Processing stats:", stats)

asyncio.run(development_example())
```

## Integration Examples

### 11. FastAPI Integration

```python
from fastapi import FastAPI, BackgroundTasks
from streamflow import StreamFlow

app = FastAPI()
sf = StreamFlow()

@app.on_event("startup")
async def startup():
    await sf.start_ingestion_service()

@app.post("/events")
async def create_event(event_data: dict, background_tasks: BackgroundTasks):
    event = Event(
        type=event_data["type"],
        data=event_data["data"],
        timestamp=datetime.utcnow()
    )
    
    # Process in background
    background_tasks.add_task(sf.ingestion.send_event, event)
    
    return {"status": "accepted"}

@app.get("/metrics")
async def get_metrics():
    return await sf.dashboard.get_current_metrics()
```

### 12. CLI Usage

```python
# Command-line interface usage
from streamflow.cli import StreamFlowCLI

# Example CLI commands that users can run:

# Start all services
# streamflow start --all

# Start specific service
# streamflow start --service ingestion

# Send test event
# streamflow send-event --type "user.click" --data '{"user_id": "123"}'

# Create alert rule
# streamflow create-alert --name "High CPU" --condition "cpu > 80" --channel email

# Get metrics
# streamflow metrics --realtime

# Export data
# streamflow export --start "2023-01-01" --end "2023-01-02" --format json
```

## Error Handling and Best Practices

### 13. Robust Error Handling

```python
from streamflow.exceptions import StreamFlowException, EventValidationError

async def robust_event_handling():
    sf = StreamFlow()
    
    try:
        # Send event with potential validation errors
        event = Event(
            type="user.action",
            data={"user_id": None},  # This might cause validation error
            timestamp=datetime.utcnow()
        )
        
        await sf.ingestion.send_event(event)
        
    except EventValidationError as e:
        print(f"Event validation failed: {e}")
        # Handle validation error - maybe log and continue
        
    except StreamFlowException as e:
        print(f"StreamFlow error: {e}")
        # Handle StreamFlow-specific errors
        
    except Exception as e:
        print(f"Unexpected error: {e}")
        # Handle other errors

asyncio.run(robust_event_handling())
```

### 14. Performance Monitoring

```python
async def performance_monitoring():
    sf = StreamFlow()
    
    # Monitor performance metrics
    while True:
        stats = await sf.get_performance_stats()
        
        print(f"Events/sec: {stats['events_per_second']}")
        print(f"Processing latency: {stats['avg_latency_ms']}ms")
        print(f"Queue depth: {stats['queue_depth']}")
        print(f"Memory usage: {stats['memory_usage_mb']}MB")
        
        # Check if intervention is needed
        if stats['events_per_second'] < 100:
            print("WARNING: Low throughput detected!")
        
        if stats['avg_latency_ms'] > 1000:
            print("WARNING: High latency detected!")
        
        await asyncio.sleep(10)

# Run in background for monitoring
# asyncio.create_task(performance_monitoring())
```

## Summary

StreamFlow provides a comprehensive real-time analytics pipeline with these key user-facing capabilities:

1. **Event Ingestion**: Simple API for sending events individually or in batches
2. **Real-time Analytics**: Configurable rules for stream processing and aggregations
3. **Intelligent Alerting**: Flexible alert rules with multiple notification channels
4. **Live Dashboards**: Real-time metrics and historical data visualization
5. **Production Ready**: Built-in monitoring, security, and scalability features

The library is designed to be easy to use for simple cases while providing advanced capabilities for complex real-time analytics scenarios.
