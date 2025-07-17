"""Unit tests for StreamFlow models."""

import pytest
from datetime import datetime
from uuid import uuid4

from shared.models.events import Event, EventType, EventBatch
from shared.models.alerts import Alert, AlertRule, AlertSeverity, AlertStatus
from shared.models.metrics import Metric, MetricType
from shared.models.auth import User, UserRole, UserStatus, UserCreate


class TestEventModels:
    """Test event models."""
    
    def test_event_creation(self):
        """Test basic event creation."""
        event = Event(
            type=EventType.USER_LOGIN,
            source="test-app",
            data={"user_id": "123"}
        )
        
        assert event.type == EventType.USER_LOGIN
        assert event.source == "test-app"
        assert event.data == {"user_id": "123"}
        assert event.id is not None
        assert isinstance(event.timestamp, datetime)
    
    def test_event_validation(self):
        """Test event validation."""
        # Test future timestamp validation
        future_time = datetime(2030, 1, 1)
        
        with pytest.raises(ValueError, match="timestamp cannot be in the future"):
            Event(
                type=EventType.USER_LOGIN,
                source="test-app",
                timestamp=future_time
            )
    
    def test_event_data_validation(self):
        """Test event data validation."""
        with pytest.raises(ValueError, match="Event data must be a dictionary"):
            Event(
                type=EventType.USER_LOGIN,
                source="test-app",
                data="invalid-data"
            )
    
    def test_event_batch_creation(self):
        """Test event batch creation."""
        events = [
            Event(type=EventType.USER_LOGIN, source="app1"),
            Event(type=EventType.USER_LOGOUT, source="app2")
        ]
        
        batch = EventBatch(events=events)
        
        assert len(batch.events) == 2
        assert batch.batch_id is not None
        assert isinstance(batch.created_at, datetime)
    
    def test_event_batch_validation(self):
        """Test event batch validation."""
        # Test empty batch
        with pytest.raises(ValueError, match="Event batch cannot be empty"):
            EventBatch(events=[])
        
        # Test oversized batch
        large_events = [
            Event(type=EventType.USER_LOGIN, source="app") 
            for _ in range(1001)
        ]
        
        with pytest.raises(ValueError, match="cannot contain more than 1000 events"):
            EventBatch(events=large_events)


class TestAlertModels:
    """Test alert models."""
    
    def test_alert_rule_creation(self):
        """Test alert rule creation."""
        rule = AlertRule(
            name="High Error Rate",
            condition="error_rate > 0.05",
            severity=AlertSeverity.HIGH,
            window="5m",
            threshold=0.05,
            created_by="admin"
        )
        
        assert rule.name == "High Error Rate"
        assert rule.severity == AlertSeverity.HIGH
        assert rule.enabled is True
        assert rule.id is not None
    
    def test_alert_rule_validation(self):
        """Test alert rule validation."""
        # Test empty condition
        with pytest.raises(ValueError, match="Alert condition cannot be empty"):
            AlertRule(
                name="Test Rule",
                condition="",
                window="5m",
                threshold=0.05,
                created_by="admin"
            )
        
        # Test invalid window format
        with pytest.raises(ValueError, match="Invalid window format"):
            AlertRule(
                name="Test Rule",
                condition="value > 10",
                window="invalid",
                threshold=0.05,
                created_by="admin"
            )
    
    def test_alert_creation(self):
        """Test alert creation."""
        rule_id = uuid4()
        alert = Alert(
            rule_id=rule_id,
            rule_name="Test Rule",
            severity=AlertSeverity.HIGH,
            message="Test alert message"
        )
        
        assert alert.rule_id == rule_id
        assert alert.status == AlertStatus.ACTIVE
        assert alert.notification_sent is False
        assert alert.id is not None
    
    def test_alert_resolved_validation(self):
        """Test alert resolved time validation."""
        triggered_time = datetime.utcnow()
        
        with pytest.raises(ValueError, match="Resolved time cannot be before triggered time"):
            Alert(
                rule_id=uuid4(),
                rule_name="Test",
                severity=AlertSeverity.LOW,
                message="Test",
                triggered_at=triggered_time,
                resolved_at=datetime(2020, 1, 1)  # Past date
            )


class TestMetricModels:
    """Test metric models."""
    
    def test_metric_creation(self):
        """Test metric creation."""
        metric = Metric(
            name="http_requests_total",
            type=MetricType.COUNTER,
            value=1234.0,
            source="web-server"
        )
        
        assert metric.name == "http_requests_total"
        assert metric.type == MetricType.COUNTER
        assert metric.value == 1234.0
        assert metric.id is not None
    
    def test_metric_name_validation(self):
        """Test metric name validation."""
        # Test invalid metric name
        with pytest.raises(ValueError, match="Invalid metric name format"):
            Metric(
                name="invalid-metric-name!",
                type=MetricType.GAUGE,
                value=100.0,
                source="test"
            )
    
    def test_metric_labels_validation(self):
        """Test metric labels validation."""
        # Test invalid label types
        with pytest.raises(ValueError, match="Label keys and values must be strings"):
            Metric(
                name="test_metric",
                type=MetricType.GAUGE,
                value=100.0,
                source="test",
                labels={"key": 123}  # Invalid label value type
            )


class TestAuthModels:
    """Test authentication models."""
    
    def test_user_creation(self):
        """Test user creation."""
        user = User(
            username="testuser",
            email="test@example.com",
            full_name="Test User"
        )
        
        assert user.username == "testuser"
        assert user.role == UserRole.USER
        assert user.status == UserStatus.ACTIVE
        assert user.id is not None
    
    def test_username_validation(self):
        """Test username validation."""
        user = User(
            username="TestUser123",
            email="test@example.com",
            full_name="Test User"
        )
        
        # Username should be converted to lowercase
        assert user.username == "testuser123"
        
        # Test invalid username characters
        with pytest.raises(ValueError, match="Username can only contain"):
            User(
                username="invalid@username",
                email="test@example.com",
                full_name="Test User"
            )
    
    def test_user_create_validation(self):
        """Test user creation validation."""
        # Test weak password
        with pytest.raises(ValueError, match="Password must be at least 8 characters"):
            UserCreate(
                username="testuser",
                email="test@example.com",
                full_name="Test User",
                password="weak"
            )
        
        # Test password missing requirements
        with pytest.raises(ValueError, match="Password must contain at least one uppercase"):
            UserCreate(
                username="testuser",
                email="test@example.com",
                full_name="Test User",
                password="alllowercase123"
            )
        
        with pytest.raises(ValueError, match="Password must contain at least one digit"):
            UserCreate(
                username="testuser",
                email="test@example.com",
                full_name="Test User",
                password="NoDigitsHere"
            )
    
    def test_valid_user_create(self):
        """Test valid user creation."""
        user_create = UserCreate(
            username="testuser",
            email="test@example.com",
            full_name="Test User",
            password="ValidPass123"
        )
        
        assert user_create.username == "testuser"
        assert user_create.password == "ValidPass123"