# 📦 StreamFlow Pip Package Usage Guide

## What You Can Do After `pip install streamflow`

After installing StreamFlow via pip, you get **full event processing capabilities** without needing Docker. Here's exactly what you can do:

---

## 🚀 **1. CLI Commands (Available Immediately)**

```bash
# Install and use right away
pip install streamflow

# Check available commands
streamflow --help

# Send test events
streamflow send-event --type web.click --count 5
streamflow send-event --type user.login --source "mobile-app"
streamflow send-event --type api.request --count 10

# Start individual services
streamflow start --service ingestion --port 8001
streamflow start --service dashboard --port 8004
streamflow start --service analytics

# Check service status
streamflow status
streamflow health

# Initialize database
streamflow init-db
```

---

## 📤 **2. Send Events (YES - You Can!)**

### Via CLI
```bash
# Send web click events
streamflow send-event --type web.click --count 5

# Send user login events  
streamflow send-event --type user.login --source "web-app"

# Send API request events
streamflow send-event --type api.request --count 10

# Send custom events
streamflow send-event --type custom --source "my-system"
```

### Via Python Code
```python
import asyncio
from streamflow.shared.models import Event, EventType
from streamflow.shared.messaging import get_event_publisher

async def send_events():
    # Get event publisher
    publisher = await get_event_publisher()
    
    # Create and send events
    event = Event(
        type=EventType.WEB_CLICK,
        source="my-website",
        data={
            "page": "/home",
            "user_id": "user123",
            "timestamp": "2024-01-15T10:30:00Z"
        },
        user_id="user123",
        session_id="session456"
    )
    
    await publisher.publish_event(event)
    print(f"✅ Event sent: {event.id}")

# Run it
asyncio.run(send_events())
```

---

## 📥 **3. Receive/Process Events (YES - You Can!)**

### Start Event Processing Services
```bash
# Start ingestion service (receives events)
streamflow start --service ingestion --port 8001

# Start analytics service (processes events)  
streamflow start --service analytics

# Start alerting service (monitors events)
streamflow start --service alerting
```

### Custom Event Processing
```python
import asyncio
from streamflow.shared.messaging import get_message_broker
from streamflow.shared.models import Event

async def process_events():
    # Connect to message broker
    broker = await get_message_broker()
    await broker.connect()
    
    # Define event processor
    async def handle_event(message):
        event = Event(**message.body)
        print(f"📥 Received event: {event.type} from {event.source}")
        print(f"   Data: {event.data}")
        
        # Process the event
        if event.type == "web.click":
            print("   → Processing web click analytics")
        elif event.type == "user.login":
            print("   → Updating user session tracking")
    
    # Subscribe to events
    await broker.subscribe(
        queue_name="my_event_processor",
        routing_key="events.*",
        exchange_name="streamflow.events",
        callback=handle_event
    )
    
    print("🎧 Listening for events...")
    await asyncio.sleep(3600)  # Listen for 1 hour

# Run it
asyncio.run(process_events())
```

---

## 📊 **4. Available Event Types**

```python
from streamflow.shared.models import EventType

# All supported event types:
EventType.WEB_CLICK      # "web.click"
EventType.WEB_PAGEVIEW   # "web.pageview"  
EventType.API_REQUEST    # "api.request"
EventType.API_RESPONSE   # "api.response"
EventType.USER_LOGIN     # "user.login"
EventType.USER_LOGOUT    # "user.logout"
EventType.ERROR          # "error"
EventType.METRIC         # "metric"
EventType.CUSTOM         # "custom"
```

---

## 🎯 **5. Real Examples You Can Run Now**

### Example 1: E-commerce Event Tracking
```python
import asyncio
from streamflow.shared.models import Event, EventType
from streamflow.shared.messaging import get_event_publisher

async def track_ecommerce_events():
    publisher = await get_event_publisher()
    
    # Product view
    await publisher.publish_event(Event(
        type=EventType.WEB_PAGEVIEW,
        source="ecommerce-site",
        data={"product_id": "prod123", "category": "electronics"},
        user_id="user456"
    ))
    
    # Add to cart
    await publisher.publish_event(Event(
        type=EventType.WEB_CLICK,
        source="ecommerce-site", 
        data={"action": "add_to_cart", "product_id": "prod123"},
        user_id="user456"
    ))
    
    # Purchase
    await publisher.publish_event(Event(
        type=EventType.CUSTOM,
        source="ecommerce-site",
        data={"action": "purchase", "total": 299.99},
        user_id="user456"
    ))

asyncio.run(track_ecommerce_events())
```

### Example 2: API Monitoring
```python
import asyncio
from streamflow.shared.models import Event, EventType
from streamflow.shared.messaging import get_event_publisher

async def monitor_api():
    publisher = await get_event_publisher()
    
    # API request monitoring
    await publisher.publish_event(Event(
        type=EventType.API_REQUEST,
        source="user-service",
        data={
            "endpoint": "/api/users/123",
            "method": "GET", 
            "response_time_ms": 45,
            "status_code": 200
        }
    ))
    
    # Error tracking
    await publisher.publish_event(Event(
        type=EventType.ERROR,
        source="payment-service",
        data={
            "error": "Payment failed",
            "error_code": "CARD_DECLINED"
        }
    ))

asyncio.run(monitor_api())
```

---

## 🔌 **6. What You DON'T Need Docker For**

✅ **Works without Docker:**
- ✅ Send events via CLI or Python
- ✅ Process events with custom handlers  
- ✅ Run individual services
- ✅ Development and testing
- ✅ Create custom analytics pipelines
- ✅ Build alerts and monitoring

❌ **Needs Docker:**
- Complete production infrastructure
- Pre-configured databases (PostgreSQL, Redis)
- Message broker (RabbitMQ) setup
- Web dashboard UI
- Multi-service orchestration

---

## 💡 **Quick Start in 30 Seconds**

```bash
# 1. Install
pip install streamflow

# 2. Send your first event
streamflow send-event --type web.click --count 1

# 3. Use in Python
python3 -c "
import asyncio
from streamflow.shared.models import Event, EventType
event = Event(type=EventType.WEB_CLICK, source='test', data={'page': '/home'})
print(f'Created event: {event.id}')
"
```

**🎉 You're now using StreamFlow for event processing!**