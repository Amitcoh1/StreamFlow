"""Pytest configuration and fixtures for StreamFlow tests."""

import asyncio
from datetime import datetime
from typing import AsyncGenerator, Generator
from uuid import uuid4

import pytest
import pytest_asyncio
from fastapi.testclient import TestClient
from httpx import AsyncClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from shared.models.auth import User, UserRole, UserStatus
from shared.models.events import Event, EventType
from shared.models.alerts import Alert, AlertRule, AlertSeverity, AlertStatus
from shared.models.metrics import Metric, MetricType
from shared.utils.config import get_settings


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def settings():
    """Get test settings."""
    return get_settings()


@pytest.fixture
def test_user() -> User:
    """Create a test user."""
    return User(
        id=uuid4(),
        username="testuser",
        email="test@example.com",
        full_name="Test User",
        role=UserRole.USER,
        status=UserStatus.ACTIVE,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
        permissions=["metrics:read", "events:read", "dashboards:read"]
    )


@pytest.fixture
def admin_user() -> User:
    """Create an admin test user."""
    return User(
        id=uuid4(),
        username="admin",
        email="admin@example.com",
        full_name="Admin User",
        role=UserRole.ADMIN,
        status=UserStatus.ACTIVE,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
        permissions=[
            "users:read", "users:write", "users:delete",
            "alerts:read", "alerts:write", "alerts:delete",
            "metrics:read", "metrics:write",
            "events:read", "events:write",
            "dashboards:read", "dashboards:write", "dashboards:delete",
            "settings:read", "settings:write"
        ]
    )


@pytest.fixture
def sample_event() -> Event:
    """Create a sample event for testing."""
    return Event(
        id=uuid4(),
        type=EventType.USER_LOGIN,
        source="test-app",
        data={"user_id": "123", "ip_address": "192.168.1.1"},
        timestamp=datetime.utcnow(),
        user_id="123",
        session_id="session-123"
    )


@pytest.fixture
def sample_alert_rule() -> AlertRule:
    """Create a sample alert rule for testing."""
    return AlertRule(
        id=uuid4(),
        name="High Error Rate",
        description="Alert when error rate exceeds threshold",
        condition="error_rate > 0.05",
        severity=AlertSeverity.HIGH,
        window="5m",
        threshold=0.05,
        channels=["email"],
        enabled=True,
        created_by="admin"
    )


@pytest.fixture
def sample_alert(sample_alert_rule: AlertRule) -> Alert:
    """Create a sample alert for testing."""
    return Alert(
        id=uuid4(),
        rule_id=sample_alert_rule.id,
        rule_name=sample_alert_rule.name,
        status=AlertStatus.ACTIVE,
        severity=sample_alert_rule.severity,
        message="Error rate is 7.5% which exceeds threshold of 5%",
        details={"current_rate": 0.075, "threshold": 0.05},
        triggered_at=datetime.utcnow()
    )


@pytest.fixture
def sample_metric() -> Metric:
    """Create a sample metric for testing."""
    return Metric(
        id=uuid4(),
        name="http_requests_total",
        type=MetricType.COUNTER,
        value=1234.0,
        labels={"method": "GET", "status": "200"},
        timestamp=datetime.utcnow(),
        source="web-server",
        description="Total HTTP requests",
        unit="requests"
    )


@pytest.fixture
def auth_headers(test_user: User) -> dict:
    """Create authentication headers for testing."""
    from shared.utils.auth import create_access_token
    
    token_data = {
        "sub": str(test_user.id),
        "user_id": str(test_user.id),
        "username": test_user.username,
        "role": test_user.role,
        "permissions": test_user.permissions
    }
    
    access_token = create_access_token(token_data)
    
    return {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }


@pytest.fixture
def admin_auth_headers(admin_user: User) -> dict:
    """Create admin authentication headers for testing."""
    from shared.utils.auth import create_access_token
    
    token_data = {
        "sub": str(admin_user.id),
        "user_id": str(admin_user.id),
        "username": admin_user.username,
        "role": admin_user.role,
        "permissions": admin_user.permissions
    }
    
    access_token = create_access_token(token_data)
    
    return {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }


@pytest.fixture
async def async_client() -> AsyncGenerator[AsyncClient, None]:
    """Create an async HTTP client for testing."""
    async with AsyncClient(base_url="http://test") as client:
        yield client


@pytest.fixture
def mock_websocket():
    """Create a mock WebSocket for testing."""
    class MockWebSocket:
        def __init__(self):
            self.messages = []
            self.closed = False
        
        async def send_text(self, data: str):
            self.messages.append(data)
        
        async def close(self):
            self.closed = True
    
    return MockWebSocket()


@pytest.fixture
def mock_rabbitmq():
    """Create a mock RabbitMQ connection for testing."""
    class MockRabbitMQ:
        def __init__(self):
            self.published_messages = []
            self.connected = True
        
        async def publish(self, message: dict, routing_key: str):
            self.published_messages.append({
                "message": message,
                "routing_key": routing_key
            })
        
        async def close(self):
            self.connected = False
    
    return MockRabbitMQ()


@pytest.fixture
def mock_redis():
    """Create a mock Redis connection for testing."""
    class MockRedis:
        def __init__(self):
            self.data = {}
        
        async def get(self, key: str):
            return self.data.get(key)
        
        async def set(self, key: str, value: str, ex: int = None):
            self.data[key] = value
        
        async def delete(self, key: str):
            if key in self.data:
                del self.data[key]
    
    return MockRedis()


# Performance test helpers
@pytest.fixture
def performance_events(count: int = 1000) -> list[Event]:
    """Generate multiple events for performance testing."""
    events = []
    for i in range(count):
        event = Event(
            type=EventType.API_REQUEST,
            source=f"service-{i % 10}",
            data={"request_id": f"req-{i}", "duration_ms": i * 10},
            user_id=f"user-{i % 100}"
        )
        events.append(event)
    return events


# Integration test helpers
@pytest.fixture
def integration_test_data():
    """Provide test data for integration tests."""
    return {
        "events": [
            {"type": "user.login", "source": "web", "data": {"user_id": "1"}},
            {"type": "api.request", "source": "mobile", "data": {"endpoint": "/api/data"}},
            {"type": "system.error", "source": "analytics", "data": {"error": "connection_failed"}},
        ],
        "alert_rules": [
            {
                "name": "High CPU Usage",
                "condition": "cpu_usage > 80",
                "severity": "high",
                "window": "5m",
                "threshold": 80.0
            },
            {
                "name": "Low Disk Space",
                "condition": "disk_usage > 90",
                "severity": "critical",
                "window": "1m",
                "threshold": 90.0
            }
        ]
    }