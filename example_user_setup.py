#!/usr/bin/env python3
"""
Example: Using StreamFlow with Existing Infrastructure
=====================================================

This example shows how a user with existing RabbitMQ, PostgreSQL, and Redis
would configure and use StreamFlow via pip install.

Prerequisites:
- RabbitMQ running on your-rabbitmq-server:5672
- PostgreSQL running on your-postgres-server:5432  
- Redis running on your-redis-server:6379
"""

import os
import asyncio
from datetime import datetime

# Step 1: Configure your infrastructure connection
# This would normally be in a .env file or environment variables
os.environ.update({
    # Your existing RabbitMQ server
    "RABBITMQ_URL": "amqp://myuser:mypass@your-rabbitmq-server:5672/streamflow_vhost",
    
    # Your existing PostgreSQL database
    "DATABASE_URL": "postgresql+asyncpg://dbuser:dbpass@your-postgres-server:5432/streamflow_db",
    
    # Your existing Redis cache
    "REDIS_URL": "redis://your-redis-server:6379/1",
    
    # Security settings (required)
    "JWT_SECRET_KEY": "your-company-secret-key-minimum-32-characters-long",
    
    # Optional: Custom service ports
    "INGESTION_PORT": "8001",
    "DASHBOARD_PORT": "8004"
})

# Step 2: Now you can use StreamFlow
from streamflow.shared.models import Event, EventType, EventSeverity
from streamflow.shared.messaging import get_event_publisher
from streamflow.shared.config import get_settings

async def demo_streamflow_with_existing_infrastructure():
    """Demonstrate using StreamFlow with your existing infrastructure"""
    
    print("🔧 StreamFlow with Existing Infrastructure Demo")
    print("=" * 50)
    
    # Check configuration
    settings = get_settings()
    print(f"📡 RabbitMQ: {settings.rabbitmq.url}")
    print(f"🗄️  Database: {settings.database.url}")
    print(f"💾 Redis: {settings.redis.url}")
    print()
    
    # Get event publisher (connects to your RabbitMQ)
    print("📤 Connecting to your infrastructure...")
    try:
        publisher = await get_event_publisher()
        print("✅ Connected successfully!")
    except Exception as e:
        print(f"❌ Connection failed: {e}")
        print("💡 Make sure your RabbitMQ, PostgreSQL, and Redis are running")
        return
    
    print()
    print("📊 Sending events to your existing infrastructure:")
    
    # Example 1: E-commerce events
    print("  🛒 E-commerce events:")
    ecommerce_events = [
        Event(
            type=EventType.WEB_PAGEVIEW,
            source="your-ecommerce-app",
            data={
                "product_id": "prod_123",
                "category": "electronics",
                "price": 299.99,
                "user_agent": "Mozilla/5.0..."
            },
            user_id="user_456",
            session_id="session_789"
        ),
        Event(
            type=EventType.WEB_CLICK,
            source="your-ecommerce-app",
            data={
                "action": "add_to_cart",
                "product_id": "prod_123",
                "quantity": 2
            },
            user_id="user_456",
            session_id="session_789"
        ),
        Event(
            type=EventType.CUSTOM,
            source="your-payment-service",
            data={
                "action": "purchase_completed",
                "order_id": "order_12345",
                "total_amount": 599.98,
                "payment_method": "credit_card"
            },
            user_id="user_456",
            severity=EventSeverity.HIGH
        )
    ]
    
    for event in ecommerce_events:
        await publisher.publish_event(event)
        print(f"    ✅ {event.type.value}: {event.data}")
    
    # Example 2: API monitoring events
    print("  🌐 API monitoring events:")
    api_events = [
        Event(
            type=EventType.API_REQUEST,
            source="your-user-service",
            data={
                "endpoint": "/api/v1/users/profile",
                "method": "GET",
                "status_code": 200,
                "response_time_ms": 45,
                "client_ip": "192.168.1.100"
            }
        ),
        Event(
            type=EventType.ERROR,
            source="your-payment-service",
            data={
                "error_type": "payment_declined",
                "error_code": "INSUFFICIENT_FUNDS",
                "endpoint": "/api/v1/payments/charge",
                "user_id": "user_789"
            },
            severity=EventSeverity.CRITICAL
        )
    ]
    
    for event in api_events:
        await publisher.publish_event(event)
        print(f"    ✅ {event.type.value}: {event.data['endpoint'] if 'endpoint' in event.data else 'error'}")
    
    # Example 3: Custom business events
    print("  📈 Custom business events:")
    business_events = [
        Event(
            type=EventType.CUSTOM,
            source="your-analytics-service",
            data={
                "metric_name": "daily_active_users",
                "value": 15420,
                "date": datetime.now().isoformat(),
                "region": "us-east-1"
            }
        ),
        Event(
            type=EventType.METRIC,
            source="your-infrastructure-monitoring",
            data={
                "metric": "cpu_usage_percent",
                "value": 78.5,
                "host": "web-server-01",
                "timestamp": datetime.now().isoformat()
            }
        )
    ]
    
    for event in business_events:
        await publisher.publish_event(event)
        print(f"    ✅ {event.type.value}: {event.data.get('metric_name', event.data.get('metric', 'custom'))}")
    
    print()
    print("🎉 All events sent to your infrastructure!")
    print("📊 Events are now flowing through:")
    print("   • Your RabbitMQ server (queued for processing)")
    print("   • Available for your analytics services")
    print("   • Ready for real-time alerts and monitoring")
    print()
    print("🚀 Next steps:")
    print("   • Start StreamFlow services: streamflow start --service analytics")
    print("   • Monitor with: streamflow status")
    print("   • View dashboard: streamflow start --service dashboard --port 8004")

if __name__ == "__main__":
    print("🏗️  Example: StreamFlow with Your Existing Infrastructure")
    print()
    print("📋 This example assumes you have:")
    print("   • RabbitMQ running on your-rabbitmq-server:5672")
    print("   • PostgreSQL running on your-postgres-server:5432")
    print("   • Redis running on your-redis-server:6379")
    print()
    print("⚙️  Configuration is set via environment variables above")
    print("   (In real usage, put these in a .env file)")
    print()
    
    # Run the demo
    asyncio.run(demo_streamflow_with_existing_infrastructure())