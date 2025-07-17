#!/usr/bin/env python3
"""
StreamFlow Integration Example
============================

This example shows how to integrate StreamFlow with your existing systems.
Run this after starting StreamFlow with './start.sh'

 
"""

import asyncio
import json
import websockets
from datetime import datetime, timezone
from typing import Dict, Any

# Note: requests is used for synchronous HTTP calls
try:
    import requests
except ImportError:
    requests = None
    print("Warning: requests package not found. Install with: pip install requests")

# Note: aiohttp is used for asynchronous HTTP calls
try:
    import aiohttp
except ImportError:
    aiohttp = None
    print("Warning: aiohttp package not found. Install with: pip install aiohttp")

class StreamFlowClient:
    """Simple client for integrating with StreamFlow"""
    
    def __init__(self, base_url: str = "http://localhost"):
        self.base_url = base_url
        self.ingestion_url = f"{base_url}:8001"
        self.analytics_url = f"{base_url}:8002"
        self.alerting_url = f"{base_url}:8003"
        self.dashboard_url = f"{base_url}:8004"
        self.storage_url = f"{base_url}:8005"
    
    def send_event(self, event_data: Dict[str, Any]) -> Dict[str, Any]:
        """Send an event to StreamFlow"""
        try:
            response = requests.post(
                f"{self.ingestion_url}/events",
                json=event_data,
                headers={"Content-Type": "application/json"},
                timeout=10
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"Error sending event: {e}")
            return {"error": str(e)}
    
    def create_alert_rule(self, rule_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create an alert rule"""
        try:
            response = requests.post(
                f"{self.alerting_url}/alerts/rules",
                json=rule_data,
                headers={"Content-Type": "application/json"},
                timeout=10
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"Error creating alert rule: {e}")
            return {"error": str(e)}
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get real-time metrics"""
        try:
            response = requests.get(
                f"{self.dashboard_url}/metrics/realtime",
                timeout=10
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"Error getting metrics: {e}")
            return {"error": str(e)}
    
    def check_health(self) -> Dict[str, bool]:
        """Check health of all services"""
        services = {
            "ingestion": self.ingestion_url,
            "analytics": self.analytics_url,
            "alerting": self.alerting_url,
            "dashboard": self.dashboard_url,
            "storage": self.storage_url
        }
        
        health_status = {}
        for service, url in services.items():
            try:
                if requests is None:
                    health_status[service] = False
                    continue
                response = requests.get(f"{url}/health", timeout=5)
                health_status[service] = response.status_code == 200
            except (requests.exceptions.RequestException, Exception) as e:
                print(f"Health check failed for {service}: {e}")
                health_status[service] = False
        
        return health_status

def example_ecommerce_integration():
    """Example: E-commerce website integration"""
    print("🛒 E-commerce Integration Example")
    print("=" * 40)
    
    client = StreamFlowClient()
    
    # Simulate user journey events
    events = [
        {
            "type": "user.page_view",
            "source": "ecommerce_website",
            "data": {
                "user_id": "user123",
                "page": "/products/laptop",
                "session_id": "session456",
                "user_agent": "Mozilla/5.0...",
                "referrer": "https://google.com"
            },
            "severity": "low",
            "tags": ["frontend", "pageview"]
        },
        {
            "type": "user.add_to_cart",
            "source": "ecommerce_website",
            "data": {
                "user_id": "user123",
                "product_id": "laptop_001",
                "quantity": 1,
                "price": 999.99,
                "session_id": "session456"
            },
            "severity": "medium",
            "tags": ["frontend", "conversion"]
        },
        {
            "type": "user.purchase",
            "source": "ecommerce_website",
            "data": {
                "user_id": "user123",
                "order_id": "order789",
                "total_amount": 999.99,
                "payment_method": "credit_card",
                "session_id": "session456"
            },
            "severity": "high",
            "tags": ["frontend", "conversion", "revenue"]
        }
    ]
    
    # Send events
    for event in events:
        event["timestamp"] = datetime.now(timezone.utc).isoformat()
        result = client.send_event(event)
        print(f"Sent {event['type']}: {result}")
    
    # Create alert for abandoned carts
    alert_rule = {
        "name": "Cart Abandonment Alert",
        "condition": "type == 'user.add_to_cart' and not exists(type == 'user.purchase')",
        "window_seconds": 1800,  # 30 minutes
        "channels": ["email"],
        "template": "User {{data.user_id}} added items to cart but didn't purchase",
        "recipients": ["marketing@company.com"]
    }
    
    alert_result = client.create_alert_rule(alert_rule)
    print(f"Created alert rule: {alert_result}")

def example_system_monitoring():
    """Example: System monitoring integration"""
    print("\n📊 System Monitoring Example")
    print("=" * 40)
    
    client = StreamFlowClient()
    
    # Simulate system metrics
    system_events = [
        {
            "type": "system.cpu",
            "source": "server001",
            "data": {
                "usage_percent": 85.2,
                "cores": 8,
                "load_average": 3.2
            },
            "severity": "medium",
            "tags": ["monitoring", "infrastructure"]
        },
        {
            "type": "system.memory",
            "source": "server001",
            "data": {
                "used_gb": 14.5,
                "total_gb": 16.0,
                "usage_percent": 90.6
            },
            "severity": "high",
            "tags": ["monitoring", "infrastructure"]
        },
        {
            "type": "system.disk",
            "source": "server001",
            "data": {
                "used_gb": 180.5,
                "total_gb": 200.0,
                "usage_percent": 90.25
            },
            "severity": "high",
            "tags": ["monitoring", "infrastructure"]
        }
    ]
    
    # Send metrics
    for event in system_events:
        event["timestamp"] = datetime.now(timezone.utc).isoformat()
        result = client.send_event(event)
        print(f"Sent {event['type']}: {result}")
    
    # Create alert for high resource usage
    alert_rule = {
        "name": "High Resource Usage",
        "condition": "data.usage_percent > 90",
        "window_seconds": 300,  # 5 minutes
        "channels": ["slack", "email"],
        "template": "High {{type}} usage: {{data.usage_percent}}% on {{source}}",
        "recipients": ["ops@company.com"]
    }
    
    alert_result = client.create_alert_rule(alert_rule)
    print(f"Created alert rule: {alert_result}")

def example_iot_integration():
    """Example: IoT sensor data integration"""
    print("\n🌡️ IoT Sensor Integration Example")
    print("=" * 40)
    
    client = StreamFlowClient()
    
    # Simulate IoT sensor data
    sensor_events = [
        {
            "type": "sensor.temperature",
            "source": "warehouse_sensor_01",
            "data": {
                "value": 32.5,
                "unit": "celsius",
                "location": "warehouse_zone_a",
                "sensor_id": "temp_001"
            },
            "severity": "medium",
            "tags": ["iot", "environmental"]
        },
        {
            "type": "sensor.humidity",
            "source": "warehouse_sensor_01",
            "data": {
                "value": 75.2,
                "unit": "percent",
                "location": "warehouse_zone_a",
                "sensor_id": "hum_001"
            },
            "severity": "low",
            "tags": ["iot", "environmental"]
        },
        {
            "type": "sensor.pressure",
            "source": "warehouse_sensor_01",
            "data": {
                "value": 1013.25,
                "unit": "hPa",
                "location": "warehouse_zone_a",
                "sensor_id": "press_001"
            },
            "severity": "low",
            "tags": ["iot", "environmental"]
        }
    ]
    
    # Send sensor data
    for event in sensor_events:
        event["timestamp"] = datetime.now(timezone.utc).isoformat()
        result = client.send_event(event)
        print(f"Sent {event['type']}: {result}")
    
    # Create alert for temperature anomalies
    alert_rule = {
        "name": "Temperature Anomaly",
        "condition": "type == 'sensor.temperature' and (data.value > 35 or data.value < 10)",
        "window_seconds": 60,  # 1 minute
        "channels": ["webhook"],
        "template": "Temperature anomaly: {{data.value}}°C in {{data.location}}",
        "webhook_url": "https://hooks.slack.com/services/YOUR/WEBHOOK/URL"
    }
    
    alert_result = client.create_alert_rule(alert_rule)
    print(f"Created alert rule: {alert_result}")

async def example_realtime_streaming():
    """Example: Real-time streaming via WebSocket"""
    print("\n🔄 Real-time Streaming Example")
    print("=" * 40)
    
    try:
        uri = "ws://localhost:8001/events/stream"
        async with websockets.connect(uri) as websocket:
            # Send real-time events
            for i in range(5):
                event = {
                    "type": "user.activity",
                    "source": "mobile_app",
                    "data": {
                        "user_id": f"user{i}",
                        "activity": "scroll",
                        "screen": "home",
                        "timestamp": datetime.now(timezone.utc).isoformat()
                    },
                    "severity": "low",
                    "tags": ["mobile", "user-activity"]
                }
                
                await websocket.send(json.dumps(event))
                print(f"Sent real-time event {i+1}")
                
                # Wait for response
                response = await asyncio.wait_for(websocket.recv(), timeout=5.0)
                print(f"Received: {response}")
                
                await asyncio.sleep(1)
                
    except Exception as e:
        print(f"WebSocket error: {e}")
        print("Make sure StreamFlow is running with './start.sh'")

def main():
    """Main function to run all examples"""
    print("🌊 StreamFlow Integration Examples")
    print("=" * 50)
    
    client = StreamFlowClient()
    
    # Check if services are running
    print("\n🔍 Checking service health...")
    health_status = client.check_health()
    for service, is_healthy in health_status.items():
        status = "✅ Healthy" if is_healthy else "❌ Unhealthy"
        print(f"  {service}: {status}")
    
    if not all(health_status.values()):
        print("\n⚠️  Some services are not healthy.")
        print("Please run './start.sh' to start StreamFlow first.")
        return
    
    # Run examples
    try:
        example_ecommerce_integration()
        example_system_monitoring()
        example_iot_integration()
        
        print("\n🔄 Testing real-time streaming...")
        asyncio.run(example_realtime_streaming())
        
    except KeyboardInterrupt:
        print("\n\n👋 Examples interrupted by user")
    except Exception as e:
        print(f"\n❌ Error running examples: {e}")
    
    # Show final metrics
    print("\n📊 Final Metrics:")
    metrics = client.get_metrics()
    if "error" not in metrics:
        print(json.dumps(metrics, indent=2))
    else:
        print(f"Error getting metrics: {metrics['error']}")
    
    print("\n✅ Integration examples completed!")
    print("Check the StreamFlow dashboard at http://localhost:8004")

if __name__ == "__main__":
    main()
