"""
StreamFlow Usage Examples
========================

This file contains comprehensive examples of how to use StreamFlow
for real-time analytics pipeline development.

StreamFlow - real-time analytics pipeline
 
"""

import asyncio
import json
from datetime import datetime, timedelta
from typing import List, Dict, Any

# Example 1: Basic Event Creation and Publishing
async def example_basic_event_publishing():
    """
    Example 1: Basic Event Creation and Publishing
    
    This example shows how to create and publish events to StreamFlow.
    """
    print("🚀 Example 1: Basic Event Publishing")
    
    from streamflow.shared.models import Event, EventType, EventSeverity
    from streamflow.shared.messaging import get_event_publisher
    
    # Create an event publisher
    publisher = await get_event_publisher()
    
    # Create a simple web click event
    click_event = Event(
        type=EventType.WEB_CLICK,
        source="website",
        data={
            "page": "/dashboard",
            "user_id": "user123",
            "session_id": "session456",
            "coordinates": {"x": 100, "y": 200},
            "element": "button.submit"
        },
        severity=EventSeverity.LOW,
        tags=["frontend", "user-interaction"]
    )
    
    # Publish the event
    await publisher.publish_event(click_event)
    print(f"✅ Published click event: {click_event.id}")
    
    # Create an API request event
    api_event = Event(
        type=EventType.API_REQUEST,
        source="api-gateway",
        data={
            "endpoint": "/api/users",
            "method": "POST",
            "status_code": 201,
            "response_time": 0.045,
            "user_id": "user123"
        },
        severity=EventSeverity.MEDIUM,
        correlation_id="corr-789"
    )
    
    await publisher.publish_event(api_event)
    print(f"✅ Published API event: {api_event.id}")


# Example 2: Batch Event Processing
async def example_batch_event_processing():
    """
    Example 2: Batch Event Processing
    
    This example demonstrates how to process multiple events in batch.
    """
    print("\n🚀 Example 2: Batch Event Processing")
    
    from streamflow.shared.models import Event, EventType
    from streamflow.shared.messaging import get_event_publisher
    
    publisher = await get_event_publisher()
    
    # Create a batch of user login events
    login_events = []
    for i in range(10):
        event = Event(
            type=EventType.USER_LOGIN,
            source="auth-service",
            data={
                "user_id": f"user{i:03d}",
                "ip_address": f"192.168.1.{i + 1}",
                "user_agent": "Mozilla/5.0 (Web Browser)",
                "login_method": "password",
                "device_type": "desktop" if i % 2 == 0 else "mobile"
            },
            tags=["authentication", "security"]
        )
        login_events.append(event)
    
    # Publish events concurrently
    tasks = [publisher.publish_event(event) for event in login_events]
    await asyncio.gather(*tasks)
    
    print(f"✅ Published {len(login_events)} login events")


# Example 3: Real-time Analytics Pipeline
async def example_analytics_pipeline():
    """
    Example 3: Real-time Analytics Pipeline
    
    This example shows how to set up a custom analytics pipeline.
    """
    print("\n🚀 Example 3: Real-time Analytics Pipeline")
    
    from streamflow.services.analytics.main import StreamProcessor
    from streamflow.shared.models import Event, EventType, MetricType
    
    # Create a stream processor
    processor = StreamProcessor()
    
    # Register custom time windows
    processor.register_window("30sec", 30)
    processor.register_window("2min", 120)
    processor.register_window("10min", 600)
    
    # Register custom aggregators
    def average_response_time(events: List[Event]) -> float:
        """Calculate average response time from API events"""
        api_events = [e for e in events if e.type == EventType.API_REQUEST]
        if not api_events:
            return 0.0
        
        total_time = sum(e.data.get("response_time", 0) for e in api_events)
        return total_time / len(api_events)
    
    def error_rate(events: List[Event]) -> float:
        """Calculate error rate from all events"""
        if not events:
            return 0.0
        
        error_events = [e for e in events if e.type == EventType.ERROR]
        return len(error_events) / len(events)
    
    processor.register_aggregator("avg_response_time", average_response_time)
    processor.register_aggregator("error_rate", error_rate)
    
    # Register custom rules
    async def handle_slow_api(event: Event) -> Dict[str, Any]:
        """Handle slow API response"""
        response_time = event.data.get("response_time", 0)
        return {
            "alert_type": "slow_api",
            "message": f"Slow API response detected: {response_time}s",
            "threshold": 1.0,
            "actual_value": response_time
        }
    
    async def handle_high_error_rate(event: Event) -> Dict[str, Any]:
        """Handle high error rate"""
        window = processor.windows.get("2min")
        if window:
            current_error_rate = error_rate(window.get_events())
            if current_error_rate > 0.1:  # 10% error rate
                return {
                    "alert_type": "high_error_rate",
                    "message": f"High error rate: {current_error_rate:.2%}",
                    "threshold": 0.1,
                    "actual_value": current_error_rate
                }
        return {}
    
    processor.register_rule(
        "slow_api_detection",
        "event_type == 'api.request' and event.data.get('response_time', 0) > 1.0",
        handle_slow_api
    )
    
    processor.register_rule(
        "error_rate_monitoring",
        "event_type == 'error'",
        handle_high_error_rate
    )
    
    # Simulate processing some events
    test_events = [
        Event(
            type=EventType.API_REQUEST,
            source="api-service",
            data={"endpoint": "/api/users", "response_time": 0.5}
        ),
        Event(
            type=EventType.API_REQUEST,
            source="api-service",
            data={"endpoint": "/api/orders", "response_time": 1.5}  # Slow!
        ),
        Event(
            type=EventType.ERROR,
            source="payment-service",
            data={"error": "Payment failed", "code": 500}
        )
    ]
    
    for event in test_events:
        results = await processor.process_event(event)
        print(f"  📊 Processed event {event.id}: {len(results)} results")
        
        for result in results:
            if result.output:
                print(f"    🚨 Alert: {result.output}")


# Example 4: Custom Alert Rules
async def example_custom_alert_rules():
    """
    Example 4: Custom Alert Rules
    
    This example shows how to create custom alert rules.
    """
    print("\n🚀 Example 4: Custom Alert Rules")
    
    from streamflow.shared.models import AlertRule, AlertLevel, AlertChannel
    
    # Create alert rules
    alert_rules = [
        AlertRule(
            name="High CPU Usage",
            description="Alert when CPU usage exceeds 80%",
            condition="metric.name == 'cpu_usage' and metric.value > 80",
            threshold=80.0,
            window="5m",
            level=AlertLevel.WARNING,
            channels=[AlertChannel.EMAIL, AlertChannel.SLACK],
            suppression_minutes=10
        ),
        AlertRule(
            name="Critical Memory Usage",
            description="Alert when memory usage exceeds 95%",
            condition="metric.name == 'memory_usage' and metric.value > 95",
            threshold=95.0,
            window="1m",
            level=AlertLevel.CRITICAL,
            channels=[AlertChannel.EMAIL, AlertChannel.SLACK, AlertChannel.SMS],
            escalation_minutes=5
        ),
        AlertRule(
            name="Database Connection Pool Full",
            description="Alert when database connection pool is full",
            condition="metric.name == 'db_connections' and metric.value >= 100",
            threshold=100.0,
            window="30s",
            level=AlertLevel.ERROR,
            channels=[AlertChannel.WEBHOOK],
            metadata={"webhook_url": "https://api.example.com/alerts"}
        )
    ]
    
    for rule in alert_rules:
        print(f"  📋 Created alert rule: {rule.name}")
        print(f"    📊 Condition: {rule.condition}")
        print(f"    🔔 Channels: {', '.join(rule.channels)}")
        print(f"    ⏰ Window: {rule.window}")


# Example 5: WebSocket Real-time Events
async def example_websocket_events():
    """
    Example 5: WebSocket Real-time Events
    
    This example demonstrates WebSocket integration for real-time events.
    """
    print("\n🚀 Example 5: WebSocket Real-time Events")
    
    # Note: This is a conceptual example - actual WebSocket client would be needed
    websocket_events = [
        {
            "type": "event",
            "data": {
                "event_type": "user.activity",
                "user_id": "user123",
                "action": "page_view",
                "page": "/dashboard",
                "timestamp": datetime.utcnow().isoformat()
            }
        },
        {
            "type": "event",
            "data": {
                "event_type": "system.metric",
                "metric": "active_users",
                "value": 150,
                "timestamp": datetime.utcnow().isoformat()
            }
        }
    ]
    
    for ws_event in websocket_events:
        print(f"  📡 WebSocket event: {ws_event['type']}")
        print(f"    📋 Data: {json.dumps(ws_event['data'], indent=2)}")


# Example 6: Metrics and Monitoring
async def example_metrics_monitoring():
    """
    Example 6: Metrics and Monitoring
    
    This example shows how to work with metrics and monitoring.
    """
    print("\n🚀 Example 6: Metrics and Monitoring")
    
    from streamflow.shared.models import MetricData, MetricType
    from streamflow.shared.messaging import get_event_publisher
    
    publisher = await get_event_publisher()
    
    # Create various types of metrics
    metrics = [
        MetricData(
            name="http_requests_total",
            type=MetricType.COUNTER,
            value=1,
            tags={"method": "GET", "endpoint": "/api/users", "status": "200"}
        ),
        MetricData(
            name="response_time_seconds",
            type=MetricType.HISTOGRAM,
            value=0.234,
            tags={"method": "POST", "endpoint": "/api/orders"}
        ),
        MetricData(
            name="active_connections",
            type=MetricType.GAUGE,
            value=45,
            tags={"service": "database", "instance": "primary"}
        ),
        MetricData(
            name="queue_depth",
            type=MetricType.GAUGE,
            value=123,
            tags={"queue": "analytics.events", "exchange": "events"}
        )
    ]
    
    # Publish metrics
    for metric in metrics:
        await publisher.publish_metric(metric.dict())
        print(f"  📊 Published metric: {metric.name} = {metric.value}")


# Example 7: Database Integration
async def example_database_integration():
    """
    Example 7: Database Integration
    
    This example shows database operations.
    """
    print("\n🚀 Example 7: Database Integration")
    
    from streamflow.shared.database import get_database_manager, BaseRepository, EventModel
    from streamflow.shared.models import Event, EventType
    
    # Get database manager
    db_manager = await get_database_manager()
    
    # Create a repository
    event_repo = BaseRepository(EventModel, db_manager)
    
    # Create a test event
    test_event = Event(
        type=EventType.WEB_CLICK,
        source="database_example",
        data={"page": "/example", "user_id": "db_user123"}
    )
    
    print(f"  💾 Created event for database: {test_event.id}")
    
    # In a real scenario, you would:
    # 1. Save event to database
    # 2. Query events by various criteria
    # 3. Update event status
    # 4. Get event statistics
    
    # Example queries (conceptual)
    print("  📊 Example database operations:")
    print("    - Save event to database")
    print("    - Query events by user_id")
    print("    - Get event count by type")
    print("    - Update event processing status")


# Example 8: Production Deployment
async def example_production_deployment():
    """
    Example 8: Production Deployment
    
    This example shows production deployment considerations.
    """
    print("\n🚀 Example 8: Production Deployment")
    
    # Environment configuration
    production_config = {
        "environment": "production",
        "debug": False,
        "log_level": "INFO",
        "rabbitmq": {
            "url": "amqp://user:pass@rabbitmq-cluster:5672/",
            "exchange_events": "events",
            "exchange_analytics": "analytics",
            "exchange_alerts": "alerts"
        },
        "database": {
            "url": "postgresql+asyncpg://user:pass@postgres-cluster:5432/streamflow",
            "pool_size": 20,
            "max_overflow": 30
        },
        "redis": {
            "url": "redis://redis-cluster:6379/0",
            "max_connections": 50
        },
        "security": {
            "jwt_secret_key": "production-secret-key",
            "jwt_expire_minutes": 15
        },
        "monitoring": {
            "prometheus_enabled": True,
            "jaeger_enabled": True,
            "log_format": "json"
        }
    }
    
    print("  🔧 Production Configuration:")
    for section, config in production_config.items():
        print(f"    {section}:")
        if isinstance(config, dict):
            for key, value in config.items():
                # Hide sensitive values
                if "secret" in key.lower() or "pass" in key.lower():
                    value = "***"
                print(f"      {key}: {value}")
        else:
            print(f"      {config}")
    
    # Docker deployment
    print("\n  🐳 Docker Deployment:")
    print("    docker-compose -f docker-compose.prod.yml up -d")
    
    # Kubernetes deployment
    print("\n  ☸️  Kubernetes Deployment:")
    print("    kubectl apply -f k8s/")
    print("    helm install streamflow ./helm/streamflow")
    
    # Health checks
    print("\n  🏥 Health Checks:")
    print("    curl http://ingestion-service:8001/health")
    print("    curl http://dashboard-service:8004/health")


# Example 9: Testing and Quality Assurance
async def example_testing_qa():
    """
    Example 9: Testing and Quality Assurance
    
    This example shows testing strategies.
    """
    print("\n🚀 Example 9: Testing and Quality Assurance")
    
    print("  🧪 Testing Strategy:")
    print("    - Unit Tests: Test individual components")
    print("    - Integration Tests: Test service interactions")
    print("    - Performance Tests: Load and stress testing")
    print("    - Contract Tests: API contract validation")
    print("    - End-to-End Tests: Full workflow testing")
    
    print("\n  📊 Quality Metrics:")
    print("    - Code Coverage: 90%+")
    print("    - Type Safety: mypy compliance")
    print("    - Security: bandit scanning")
    print("    - Code Quality: flake8/black formatting")
    
    print("\n  🔄 CI/CD Pipeline:")
    print("    1. Code commit → GitHub")
    print("    2. Automated tests → pytest")
    print("    3. Security scan → bandit")
    print("    4. Build images → Docker")
    print("    5. Deploy to staging → Kubernetes")
    print("    6. Integration tests → pytest")
    print("    7. Deploy to production → Helm")


# Example 10: Advanced Features
async def example_advanced_features():
    """
    Example 10: Advanced Features
    
    This example demonstrates advanced StreamFlow features.
    """
    print("\n🚀 Example 10: Advanced Features")
    
    print("  🔄 Circuit Breaker Pattern:")
    print("    - Automatic failure detection")
    print("    - Graceful degradation")
    print("    - Automatic recovery")
    
    print("\n  🔒 Security Features:")
    print("    - JWT authentication")
    print("    - Rate limiting")
    print("    - Input validation")
    print("    - CORS configuration")
    
    print("\n  📊 Observability:")
    print("    - Prometheus metrics")
    print("    - Distributed tracing")
    print("    - Structured logging")
    print("    - Health checks")
    
    print("\n  🚀 Performance Optimizations:")
    print("    - Connection pooling")
    print("    - Batch processing")
    print("    - Async/await throughout")
    print("    - Efficient serialization")
    
    print("\n  🔄 Scalability Features:")
    print("    - Horizontal scaling")
    print("    - Load balancing")
    print("    - Message queuing")
    print("    - Database sharding")


# Main function to run all examples
async def main():
    """
    Main function to run all StreamFlow examples
    """
    print("🌊 StreamFlow Examples")
    print("=" * 50)
    
    examples = [
        example_basic_event_publishing,
        example_batch_event_processing,
        example_analytics_pipeline,
        example_custom_alert_rules,
        example_websocket_events,
        example_metrics_monitoring,
        example_database_integration,
        example_production_deployment,
        example_testing_qa,
        example_advanced_features
    ]
    
    for example in examples:
        try:
            await example()
        except Exception as e:
            print(f"❌ Error in {example.__name__}: {e}")
    
    print("\n🎉 All examples completed!")
    print("\nFor more information, visit:")
    print("  📚 Documentation: https://streamflow.readthedocs.io")
    print("  💻 GitHub: https://github.com/streamflow/streamflow")
    print("  💬 Discord: https://discord.gg/streamflow")


if __name__ == "__main__":
    asyncio.run(main())
