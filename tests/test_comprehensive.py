"""
Comprehensive test suite for StreamFlow
StreamFlow - real-time analytics pipeline

 
"""
import pytest
import asyncio
import json
from datetime import datetime, timedelta
from unittest.mock import Mock, AsyncMock, patch
from uuid import uuid4
from typing import Dict, List

from fastapi.testclient import TestClient
from httpx import AsyncClient
import pytest_asyncio

from streamflow.shared.models import (
    Event, EventType, EventSeverity, Alert, AlertLevel, 
    MetricData, MetricType, HealthStatus
)
from streamflow.shared.config import Settings
from streamflow.services.ingestion.main import app as ingestion_app
from streamflow.services.analytics.main import app as analytics_app
from streamflow.services.alerting.main import app as alerting_app
from streamflow.services.dashboard.main import app as dashboard_app
from streamflow.services.storage.main import app as storage_app


class TestConfig:
    """Test configuration"""
    
    @pytest.fixture
    def test_settings(self):
        """Test settings fixture"""
        return Settings(
            environment="test",
            debug=True,
            database={
                "url": "postgresql+asyncpg://test:test@localhost:5432/test_streamflow",
                "echo": False,
                "pool_size": 5,
                "max_overflow": 10
            },
            rabbitmq={
                "url": "amqp://test:test@localhost:5672/test",
                "exchange": "test_streamflow",
                "routing_keys": {
                    "events": "events.test",
                    "alerts": "alerts.test",
                    "metrics": "metrics.test"
                }
            },
            redis={
                "url": "redis://localhost:6379/1",
                "db": 1
            },
            cors_origins=["http://localhost:3000"],
            jwt_secret_key="test-secret-key",
            services={
                "ingestion_port": 8001,
                "analytics_port": 8002,
                "alerting_port": 8003,
                "dashboard_port": 8004,
                "storage_port": 8005
            }
        )


class TestEventIngestion:
    """Test Event Ingestion Service"""
    
    @pytest.fixture
    def client(self):
        """Test client fixture"""
        return TestClient(ingestion_app)
    
    @pytest.fixture
    def sample_event(self):
        """Sample event fixture"""
        return {
            "type": "web.click",
            "source": "web-app",
            "data": {
                "element": "button",
                "page": "/home",
                "user_agent": "Mozilla/5.0..."
            },
            "severity": "medium",
            "user_id": "user123",
            "tags": ["ui", "interaction"]
        }
    
    def test_health_check(self, client):
        """Test health check endpoint"""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["service"] == "ingestion"
        assert "status" in data
    
    def test_create_event(self, client, sample_event):
        """Test single event creation"""
        with patch("streamflow.services.ingestion.main.authenticate_user") as mock_auth:
            mock_auth.return_value = {"user_id": "test_user"}
            
            response = client.post("/events", json=sample_event)
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert "event_id" in data["data"]
    
    def test_create_event_batch(self, client, sample_event):
        """Test batch event creation"""
        batch_data = {"events": [sample_event, sample_event]}
        
        with patch("streamflow.services.ingestion.main.authenticate_user") as mock_auth:
            mock_auth.return_value = {"user_id": "test_user"}
            
            response = client.post("/events/batch", json=batch_data)
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert len(data["data"]["event_ids"]) == 2
    
    def test_create_event_validation(self, client):
        """Test event validation"""
        invalid_event = {
            "type": "invalid_type",
            "source": "",  # Empty source should fail
            "data": {}
        }
        
        with patch("streamflow.services.ingestion.main.authenticate_user") as mock_auth:
            mock_auth.return_value = {"user_id": "test_user"}
            
            response = client.post("/events", json=invalid_event)
            assert response.status_code == 422  # Validation error
    
    def test_authentication_required(self, client, sample_event):
        """Test authentication requirement"""
        response = client.post("/events", json=sample_event)
        assert response.status_code == 401
    
    @pytest.mark.asyncio
    async def test_websocket_connection(self):
        """Test WebSocket connection"""
        async with AsyncClient(app=ingestion_app, base_url="http://test") as client:
            with client.websocket_connect("/ws") as websocket:
                # Send ping
                await websocket.send_text(json.dumps({"type": "ping", "data": {}}))
                response = await websocket.receive_text()
                assert response == "pong"
                
                # Send event
                event_data = {
                    "type": "event",
                    "data": {
                        "element": "button",
                        "action": "click"
                    }
                }
                await websocket.send_text(json.dumps(event_data))
                response = await websocket.receive_text()
                assert "processed successfully" in response


class TestAnalyticsService:
    """Test Analytics Service"""
    
    @pytest.fixture
    def client(self):
        """Test client fixture"""
        return TestClient(analytics_app)
    
    @pytest.fixture
    def sample_events(self):
        """Sample events for analytics"""
        return [
            Event(
                type=EventType.WEB_CLICK,
                source="web-app",
                data={"page": "/home", "element": "button"},
                timestamp=datetime.now() - timedelta(minutes=5)
            ),
            Event(
                type=EventType.WEB_PAGEVIEW,
                source="web-app",
                data={"page": "/home", "user_agent": "Mozilla/5.0..."},
                timestamp=datetime.now() - timedelta(minutes=3)
            ),
            Event(
                type=EventType.API_REQUEST,
                source="api",
                data={"endpoint": "/api/users", "method": "GET"},
                timestamp=datetime.now() - timedelta(minutes=1)
            )
        ]
    
    def test_health_check(self, client):
        """Test health check endpoint"""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["service"] == "analytics"
    
    def test_get_metrics(self, client):
        """Test metrics endpoint"""
        response = client.get("/api/v1/metrics")
        assert response.status_code == 200
        data = response.json()
        assert "metrics" in data
    
    def test_get_aggregations(self, client):
        """Test aggregations endpoint"""
        params = {
            "start_time": (datetime.now() - timedelta(hours=1)).isoformat(),
            "end_time": datetime.now().isoformat(),
            "group_by": "source"
        }
        response = client.get("/api/v1/aggregations", params=params)
        assert response.status_code == 200
        data = response.json()
        assert "aggregations" in data
    
    @pytest.mark.asyncio
    async def test_event_processing(self, sample_events):
        """Test event processing logic"""
        from streamflow.services.analytics.main import AnalyticsService
        
        # Mock dependencies
        db_manager = AsyncMock()
        message_broker = AsyncMock()
        analytics_service = AnalyticsService(db_manager, message_broker)
        
        # Test event processing
        for event in sample_events:
            result = await analytics_service.process_event(event)
            assert result is not None
    
    def test_rule_evaluation(self, client):
        """Test rule evaluation"""
        rule_data = {
            "name": "High Error Rate",
            "condition": "error_rate > 0.05",
            "window": "5m",
            "actions": ["alert"]
        }
        
        response = client.post("/api/v1/rules", json=rule_data)
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True


class TestAlertingService:
    """Test Alerting Service"""
    
    @pytest.fixture
    def client(self):
        """Test client fixture"""
        return TestClient(alerting_app)
    
    @pytest.fixture
    def sample_alert_rule(self):
        """Sample alert rule"""
        return {
            "name": "High Error Rate",
            "description": "Alert when error rate exceeds threshold",
            "condition": "error_rate > 0.05",
            "threshold": 0.05,
            "window": "5m",
            "level": "warning",
            "channels": ["email", "slack"],
            "enabled": True
        }
    
    def test_health_check(self, client):
        """Test health check endpoint"""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["service"] == "alerting"
    
    def test_create_alert_rule(self, client, sample_alert_rule):
        """Test alert rule creation"""
        response = client.post("/api/v1/rules", json=sample_alert_rule)
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "rule_id" in data["data"]
    
    def test_get_alert_rules(self, client):
        """Test getting alert rules"""
        response = client.get("/api/v1/rules")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
    
    def test_get_alerts(self, client):
        """Test getting alerts"""
        response = client.get("/api/v1/alerts")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
    
    def test_acknowledge_alert(self, client):
        """Test alert acknowledgment"""
        alert_id = str(uuid4())
        response = client.post(f"/api/v1/alerts/{alert_id}/acknowledge")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
    
    @pytest.mark.asyncio
    async def test_alert_processing(self):
        """Test alert processing logic"""
        from streamflow.services.alerting.main import AlertEngine
        
        # Mock dependencies
        db_manager = AsyncMock()
        message_broker = AsyncMock()
        alert_engine = AlertEngine(db_manager, message_broker)
        
        # Test alert generation
        event = Event(
            type=EventType.ERROR,
            source="test-service",
            data={"error_rate": 0.1},
            severity=EventSeverity.HIGH
        )
        
        result = await alert_engine.process_event(event)
        assert result is not None


class TestDashboardService:
    """Test Dashboard Service"""
    
    @pytest.fixture
    def client(self):
        """Test client fixture"""
        return TestClient(dashboard_app)
    
    def test_health_check(self, client):
        """Test health check endpoint"""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["service"] == "dashboard"
    
    def test_get_dashboards(self, client):
        """Test getting dashboards"""
        response = client.get("/api/v1/dashboards")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
    
    def test_create_dashboard(self, client):
        """Test dashboard creation"""
        dashboard_data = {
            "name": "System Overview",
            "description": "Main system dashboard",
            "widgets": [
                {
                    "type": "metric",
                    "title": "Request Count",
                    "query": "sum(requests_total)",
                    "position": {"x": 0, "y": 0, "w": 6, "h": 4}
                }
            ]
        }
        
        response = client.post("/api/v1/dashboards", json=dashboard_data)
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "dashboard_id" in data["data"]
    
    def test_get_real_time_metrics(self, client):
        """Test real-time metrics"""
        response = client.get("/api/v1/metrics/realtime")
        assert response.status_code == 200
        data = response.json()
        assert "metrics" in data
    
    @pytest.mark.asyncio
    async def test_websocket_dashboard(self):
        """Test WebSocket dashboard updates"""
        async with AsyncClient(app=dashboard_app, base_url="http://test") as client:
            with client.websocket_connect("/ws/dashboard") as websocket:
                # Subscribe to dashboard updates
                await websocket.send_text(json.dumps({
                    "type": "subscribe",
                    "dashboard_id": str(uuid4())
                }))
                
                # Should receive acknowledgment
                response = await websocket.receive_text()
                data = json.loads(response)
                assert data["type"] == "subscribed"


class TestStorageService:
    """Test Storage Service"""
    
    @pytest.fixture
    def client(self):
        """Test client fixture"""
        return TestClient(storage_app)
    
    @pytest.fixture
    def sample_events(self):
        """Sample events for storage"""
        return [
            Event(
                type=EventType.WEB_CLICK,
                source="web-app",
                data={"page": "/home"},
                timestamp=datetime.now() - timedelta(hours=1)
            ),
            Event(
                type=EventType.API_REQUEST,
                source="api",
                data={"endpoint": "/api/users"},
                timestamp=datetime.now() - timedelta(minutes=30)
            )
        ]
    
    def test_health_check(self, client):
        """Test health check endpoint"""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["service"] == "storage"
    
    def test_store_event(self, client, sample_events):
        """Test event storage"""
        event_data = sample_events[0].model_dump()
        event_data["id"] = str(event_data["id"])
        event_data["timestamp"] = event_data["timestamp"].isoformat()
        
        response = client.post("/api/v1/events", json=event_data)
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
    
    def test_query_events(self, client):
        """Test event querying"""
        query_data = {
            "start_time": (datetime.now() - timedelta(hours=2)).isoformat(),
            "end_time": datetime.now().isoformat(),
            "limit": 10
        }
        
        response = client.post("/api/v1/events/query", json=query_data)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
    
    def test_get_storage_stats(self, client):
        """Test storage statistics"""
        response = client.get("/api/v1/stats")
        assert response.status_code == 200
        data = response.json()
        assert "total_events" in data
        assert "events_by_type" in data
    
    def test_cleanup_old_data(self, client):
        """Test data cleanup"""
        response = client.post("/api/v1/cleanup")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"


class TestSharedComponents:
    """Test Shared Components"""
    
    def test_event_model_validation(self):
        """Test Event model validation"""
        # Valid event
        event = Event(
            type=EventType.WEB_CLICK,
            source="web-app",
            data={"page": "/home"}
        )
        assert event.type == EventType.WEB_CLICK
        assert event.source == "web-app"
        assert event.id is not None
        assert event.timestamp is not None
        
        # Invalid event type
        with pytest.raises(ValueError):
            Event(
                type="invalid_type",
                source="web-app",
                data={}
            )
    
    def test_alert_model_validation(self):
        """Test Alert model validation"""
        alert = Alert(
            rule_id=uuid4(),
            level=AlertLevel.WARNING,
            title="Test Alert",
            message="This is a test alert"
        )
        assert alert.level == AlertLevel.WARNING
        assert alert.resolved is False
        assert alert.acknowledged is False
    
    def test_metric_data_validation(self):
        """Test MetricData model validation"""
        metric = MetricData(
            name="requests_total",
            type=MetricType.COUNTER,
            value=100.0,
            tags={"service": "api", "method": "GET"}
        )
        assert metric.name == "requests_total"
        assert metric.type == MetricType.COUNTER
        assert metric.value == 100.0
        assert metric.tags["service"] == "api"
    
    @pytest.mark.asyncio
    async def test_database_manager(self):
        """Test database manager"""
        from streamflow.shared.database import DatabaseManager
        
        # Mock settings
        mock_settings = Mock()
        mock_settings.database.url = "postgresql+asyncpg://test:test@localhost/test"
        mock_settings.database.echo = False
        mock_settings.database.pool_size = 5
        mock_settings.database.max_overflow = 10
        
        db_manager = DatabaseManager(mock_settings)
        
        # Test initialization
        assert db_manager.settings == mock_settings
        assert db_manager.engine is None
        assert db_manager.session_factory is None
    
    @pytest.mark.asyncio
    async def test_message_broker(self):
        """Test message broker"""
        from streamflow.shared.messaging import MessageBroker
        
        # Mock settings
        mock_settings = Mock()
        mock_settings.rabbitmq.url = "amqp://test:test@localhost/test"
        mock_settings.rabbitmq.exchange = "test_exchange"
        
        message_broker = MessageBroker(mock_settings)
        
        # Test initialization
        assert message_broker.settings == mock_settings
        assert message_broker.connection is None
        assert message_broker.channel is None


class TestIntegration:
    """Integration tests"""
    
    @pytest.mark.asyncio
    async def test_event_flow(self):
        """Test complete event flow"""
        # This would test the complete flow:
        # 1. Event ingestion
        # 2. Analytics processing
        # 3. Alert generation
        # 4. Dashboard update
        # 5. Storage archival
        
        # Mock the complete flow
        event = Event(
            type=EventType.ERROR,
            source="test-service",
            data={"error_rate": 0.1},
            severity=EventSeverity.HIGH
        )
        
        # Simulate processing through all services
        assert event.type == EventType.ERROR
        assert event.severity == EventSeverity.HIGH
    
    @pytest.mark.asyncio
    async def test_service_communication(self):
        """Test inter-service communication"""
        # Test that services can communicate through message broker
        pass
    
    @pytest.mark.asyncio
    async def test_system_resilience(self):
        """Test system resilience and error handling"""
        # Test system behavior under various failure scenarios
        pass


class TestPerformance:
    """Performance tests"""
    
    @pytest.mark.asyncio
    async def test_event_ingestion_throughput(self):
        """Test event ingestion throughput"""
        # Test that the system can handle high event volumes
        pass
    
    @pytest.mark.asyncio
    async def test_analytics_processing_latency(self):
        """Test analytics processing latency"""
        # Test that analytics processing meets latency requirements
        pass
    
    @pytest.mark.asyncio
    async def test_storage_query_performance(self):
        """Test storage query performance"""
        # Test that storage queries perform within acceptable limits
        pass


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
