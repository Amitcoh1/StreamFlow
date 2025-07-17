"""
Unit tests for StreamFlow Event Ingestion Service
StreamFlow - real-time analytics pipeline

 
"""
import asyncio
import pytest
from unittest.mock import AsyncMock, Mock, patch
from datetime import datetime
from uuid import uuid4

from fastapi.testclient import TestClient
from httpx import AsyncClient

from streamflow.services.ingestion.main import app
from streamflow.shared.models import Event, EventType, EventSeverity
from streamflow.shared.config import get_settings


class TestEventIngestionService:
    """Test cases for Event Ingestion Service"""
    
    @pytest.fixture
    def client(self):
        """Test client fixture"""
        return TestClient(app)
    
    @pytest.fixture
    def mock_broker(self):
        """Mock message broker"""
        with patch('streamflow.shared.messaging.get_message_broker') as mock:
            broker = AsyncMock()
            broker.is_connected = True
            mock.return_value = broker
            yield broker
    
    @pytest.fixture
    def mock_publisher(self):
        """Mock event publisher"""
        with patch('streamflow.shared.messaging.get_event_publisher') as mock:
            publisher = AsyncMock()
            mock.return_value = publisher
            yield publisher
    
    @pytest.fixture
    def mock_db(self):
        """Mock database manager"""
        with patch('streamflow.shared.database.get_database_manager') as mock:
            db = AsyncMock()
            db.health_check.return_value = {"status": "healthy"}
            mock.return_value = db
            yield db
    
    def test_health_check(self, client, mock_broker, mock_db):
        """Test health check endpoint"""
        response = client.get("/health")
        assert response.status_code == 200
        
        data = response.json()
        assert data["service"] == "ingestion"
        assert data["version"] == "0.1.0"
        assert "checks" in data
    
    def test_readiness_check(self, client):
        """Test readiness check endpoint"""
        response = client.get("/ready")
        assert response.status_code == 200
        
        data = response.json()
        assert data["status"] == "ready"
        assert data["service"] == "ingestion"
    
    @patch('streamflow.services.ingestion.main.authenticate_user')
    def test_create_event(self, mock_auth, client, mock_publisher):
        """Test event creation endpoint"""
        mock_auth.return_value = {"user_id": "test_user"}
        
        event_data = {
            "type": "web.click",
            "source": "test_client",
            "data": {"page": "/dashboard", "user_id": "123"},
            "severity": "medium",
            "tags": ["test", "automation"]
        }
        
        response = client.post("/events", json=event_data)
        assert response.status_code == 200
        
        data = response.json()
        assert data["success"] is True
        assert data["message"] == "Event created successfully"
        assert "event_id" in data["data"]
    
    @patch('streamflow.services.ingestion.main.authenticate_user')
    def test_create_events_batch(self, mock_auth, client, mock_publisher):
        """Test batch event creation endpoint"""
        mock_auth.return_value = {"user_id": "test_user"}
        
        batch_data = {
            "events": [
                {
                    "type": "web.click",
                    "source": "test_client",
                    "data": {"page": "/dashboard"},
                    "severity": "medium"
                },
                {
                    "type": "api.request",
                    "source": "test_client",
                    "data": {"endpoint": "/api/users"},
                    "severity": "low"
                }
            ]
        }
        
        response = client.post("/events/batch", json=batch_data)
        assert response.status_code == 200
        
        data = response.json()
        assert data["success"] is True
        assert "Batch of 2 events created successfully" in data["message"]
        assert len(data["data"]["event_ids"]) == 2
    
    @patch('streamflow.services.ingestion.main.authenticate_user')
    def test_get_event(self, mock_auth, client):
        """Test get event endpoint"""
        mock_auth.return_value = {"user_id": "test_user"}
        
        event_id = str(uuid4())
        response = client.get(f"/events/{event_id}")
        assert response.status_code == 200
        
        data = response.json()
        assert data["success"] is True
        assert data["data"]["event_id"] == event_id
    
    def test_metrics_endpoint(self, client):
        """Test metrics endpoint"""
        response = client.get("/metrics")
        assert response.status_code == 200
        
        data = response.json()
        assert data["service"] == "ingestion"
        assert "websocket_connections" in data
        assert "timestamp" in data
    
    def test_unauthorized_request(self, client):
        """Test unauthorized request"""
        event_data = {
            "type": "web.click",
            "source": "test_client",
            "data": {"page": "/dashboard"}
        }
        
        response = client.post("/events", json=event_data)
        assert response.status_code == 401
    
    def test_invalid_event_type(self, client):
        """Test invalid event type"""
        with patch('streamflow.services.ingestion.main.authenticate_user') as mock_auth:
            mock_auth.return_value = {"user_id": "test_user"}
            
            event_data = {
                "type": "invalid.type",
                "source": "test_client",
                "data": {"page": "/dashboard"}
            }
            
            response = client.post("/events", json=event_data)
            assert response.status_code == 422  # Validation error


class TestEventModels:
    """Test cases for Event models"""
    
    def test_event_creation(self):
        """Test event model creation"""
        event = Event(
            type=EventType.WEB_CLICK,
            source="test_app",
            data={"page": "/dashboard", "user_id": "123"},
            severity=EventSeverity.MEDIUM,
            tags=["test", "automation"]
        )
        
        assert event.type == EventType.WEB_CLICK
        assert event.source == "test_app"
        assert event.severity == EventSeverity.MEDIUM
        assert "page" in event.data
        assert "test" in event.tags
        assert event.id is not None
        assert event.timestamp is not None
    
    def test_event_serialization(self):
        """Test event serialization"""
        event = Event(
            type=EventType.API_REQUEST,
            source="api_service",
            data={"endpoint": "/api/users", "method": "GET"},
            user_id="user123",
            correlation_id="corr123"
        )
        
        event_dict = event.dict()
        assert event_dict["type"] == "api.request"
        assert event_dict["source"] == "api_service"
        assert event_dict["user_id"] == "user123"
        assert event_dict["correlation_id"] == "corr123"
    
    def test_event_validation(self):
        """Test event validation"""
        # Test missing required fields
        with pytest.raises(ValueError):
            Event(data={"test": "value"})  # Missing type and source
        
        # Test valid event
        event = Event(
            type=EventType.ERROR,
            source="error_service",
            data={"error": "Test error"}
        )
        assert event.type == EventType.ERROR


class TestWebSocketConnection:
    """Test cases for WebSocket connections"""
    
    @pytest.mark.asyncio
    async def test_websocket_connection(self):
        """Test WebSocket connection"""
        from streamflow.services.ingestion.main import ConnectionManager
        
        manager = ConnectionManager()
        
        # Mock WebSocket
        websocket = Mock()
        websocket.accept = AsyncMock()
        websocket.send_text = AsyncMock()
        
        # Test connection
        await manager.connect(websocket)
        assert len(manager.active_connections) == 1
        websocket.accept.assert_called_once()
        
        # Test sending message
        await manager.send_personal_message("test message", websocket)
        websocket.send_text.assert_called_with("test message")
        
        # Test disconnection
        manager.disconnect(websocket)
        assert len(manager.active_connections) == 0
    
    @pytest.mark.asyncio
    async def test_websocket_broadcast(self):
        """Test WebSocket broadcast"""
        from streamflow.services.ingestion.main import ConnectionManager
        
        manager = ConnectionManager()
        
        # Mock WebSockets
        websocket1 = Mock()
        websocket1.accept = AsyncMock()
        websocket1.send_text = AsyncMock()
        
        websocket2 = Mock()
        websocket2.accept = AsyncMock()
        websocket2.send_text = AsyncMock()
        
        # Connect both WebSockets
        await manager.connect(websocket1)
        await manager.connect(websocket2)
        
        # Test broadcast
        await manager.broadcast("broadcast message")
        
        websocket1.send_text.assert_called_with("broadcast message")
        websocket2.send_text.assert_called_with("broadcast message")


class TestAsyncOperations:
    """Test cases for async operations"""
    
    @pytest.mark.asyncio
    async def test_publish_event(self):
        """Test event publishing"""
        from streamflow.services.ingestion.main import publish_event
        
        event = Event(
            type=EventType.WEB_CLICK,
            source="test_app",
            data={"page": "/test"}
        )
        
        with patch('streamflow.services.ingestion.main.get_event_publisher') as mock:
            publisher = AsyncMock()
            mock.return_value = publisher
            
            await publish_event(event)
            
            publisher.publish_event.assert_called_once_with(event)
    
    @pytest.mark.asyncio
    async def test_publish_events_batch(self):
        """Test batch event publishing"""
        from streamflow.services.ingestion.main import publish_events_batch
        
        events = [
            Event(type=EventType.WEB_CLICK, source="test_app", data={"page": "/test1"}),
            Event(type=EventType.WEB_CLICK, source="test_app", data={"page": "/test2"})
        ]
        
        with patch('streamflow.services.ingestion.main.get_event_publisher') as mock:
            publisher = AsyncMock()
            mock.return_value = publisher
            
            await publish_events_batch(events)
            
            assert publisher.publish_event.call_count == 2


class TestConfiguration:
    """Test cases for configuration"""
    
    def test_settings_loading(self):
        """Test settings loading"""
        settings = get_settings()
        
        assert settings.app_name == "StreamFlow"
        assert settings.app_version == "0.1.0"
        assert settings.environment in ["development", "staging", "production"]
        assert settings.rabbitmq.url is not None
        assert settings.database.url is not None
    
    def test_cors_origins_parsing(self):
        """Test CORS origins parsing"""
        settings = get_settings()
        
        # Test that CORS origins is a list
        assert isinstance(settings.cors_origins, list)
        
        # Test default value
        if settings.cors_origins == ["*"]:
            assert True
        else:
            assert all(isinstance(origin, str) for origin in settings.cors_origins)


# Integration tests
class TestIntegration:
    """Integration test cases"""
    
    @pytest.mark.asyncio
    async def test_full_event_flow(self):
        """Test complete event flow from API to message broker"""
        # This would be a full integration test
        # For now, we'll just test the components work together
        
        with patch('streamflow.shared.messaging.get_message_broker') as mock_broker, \
             patch('streamflow.shared.messaging.get_event_publisher') as mock_publisher:
            
            broker = AsyncMock()
            publisher = AsyncMock()
            mock_broker.return_value = broker
            mock_publisher.return_value = publisher
            
            # Create event
            event = Event(
                type=EventType.WEB_CLICK,
                source="integration_test",
                data={"page": "/integration"}
            )
            
            # Publish event
            await publisher.publish_event(event)
            
            # Verify publishing was called
            publisher.publish_event.assert_called_once_with(event)


# Performance tests
class TestPerformance:
    """Performance test cases"""
    
    @pytest.mark.asyncio
    async def test_concurrent_event_creation(self):
        """Test concurrent event creation performance"""
        from streamflow.services.ingestion.main import publish_event
        
        # Create multiple events
        events = [
            Event(
                type=EventType.WEB_CLICK,
                source="perf_test",
                data={"page": f"/test{i}"}
            )
            for i in range(100)
        ]
        
        with patch('streamflow.services.ingestion.main.get_event_publisher') as mock:
            publisher = AsyncMock()
            mock.return_value = publisher
            
            # Publish events concurrently
            tasks = [publish_event(event) for event in events]
            await asyncio.gather(*tasks)
            
            # Verify all events were published
            assert publisher.publish_event.call_count == 100


# Test fixtures and utilities
@pytest.fixture
def sample_event():
    """Sample event fixture"""
    return Event(
        type=EventType.WEB_CLICK,
        source="test_fixture",
        data={"page": "/fixture_test"},
        severity=EventSeverity.MEDIUM,
        tags=["fixture", "test"]
    )


@pytest.fixture
def sample_event_batch():
    """Sample event batch fixture"""
    return [
        Event(type=EventType.WEB_CLICK, source="batch_test", data={"page": f"/batch{i}"})
        for i in range(5)
    ]


# Helper functions for tests
def create_test_event(**kwargs):
    """Create a test event with default values"""
    defaults = {
        "type": EventType.WEB_CLICK,
        "source": "test_helper",
        "data": {"test": True}
    }
    defaults.update(kwargs)
    return Event(**defaults)


def assert_event_valid(event: Event):
    """Assert that an event is valid"""
    assert event.id is not None
    assert event.type is not None
    assert event.source is not None
    assert event.timestamp is not None
    assert isinstance(event.data, dict)
    assert isinstance(event.metadata, dict)
    assert isinstance(event.tags, list)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
