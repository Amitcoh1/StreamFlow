"""Alert models for StreamFlow."""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional
from uuid import UUID, uuid4

from pydantic import BaseModel, Field, validator


class AlertStatus(str, Enum):
    """Alert status enumeration."""
    ACTIVE = "active"
    RESOLVED = "resolved"
    SUPPRESSED = "suppressed"
    ACKNOWLEDGED = "acknowledged"


class AlertSeverity(str, Enum):
    """Alert severity levels."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class NotificationChannel(str, Enum):
    """Notification channel types."""
    EMAIL = "email"
    SLACK = "slack"
    WEBHOOK = "webhook"
    SMS = "sms"


class AlertRule(BaseModel):
    """Alert rule configuration."""
    
    id: UUID = Field(default_factory=uuid4)
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    condition: str = Field(..., description="Alert condition expression")
    severity: AlertSeverity = AlertSeverity.MEDIUM
    window: str = Field(..., description="Time window for evaluation (e.g., '5m', '1h')")
    threshold: float = Field(..., description="Threshold value for triggering alert")
    channels: List[NotificationChannel] = Field(default_factory=list)
    enabled: bool = True
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    created_by: str = Field(..., description="User who created the rule")
    
    @validator('condition')
    def validate_condition(cls, v):
        """Validate alert condition syntax."""
        if not v.strip():
            raise ValueError("Alert condition cannot be empty")
        # Basic validation - in production, use a proper expression parser
        allowed_operators = ['>', '<', '>=', '<=', '==', '!=', 'and', 'or']
        return v
    
    @validator('window')
    def validate_window(cls, v):
        """Validate time window format."""
        import re
        pattern = r'^\d+[smhd]$'  # e.g., 5m, 1h, 2d
        if not re.match(pattern, v):
            raise ValueError("Invalid window format. Use format like '5m', '1h', '2d'")
        return v


class Alert(BaseModel):
    """Alert instance."""
    
    id: UUID = Field(default_factory=uuid4)
    rule_id: UUID
    rule_name: str
    status: AlertStatus = AlertStatus.ACTIVE
    severity: AlertSeverity
    message: str = Field(..., description="Alert message")
    details: Dict[str, Any] = Field(default_factory=dict)
    triggered_at: datetime = Field(default_factory=datetime.utcnow)
    resolved_at: Optional[datetime] = None
    acknowledged_at: Optional[datetime] = None
    acknowledged_by: Optional[str] = None
    suppressed_until: Optional[datetime] = None
    notification_sent: bool = False
    notification_channels: List[NotificationChannel] = Field(default_factory=list)
    event_ids: List[UUID] = Field(default_factory=list, description="Related event IDs")
    
    @validator('resolved_at')
    def validate_resolved_at(cls, v, values):
        """Validate resolved timestamp."""
        if v and v < values.get('triggered_at', datetime.utcnow()):
            raise ValueError("Resolved time cannot be before triggered time")
        return v


class AlertHistory(BaseModel):
    """Alert history record."""
    
    id: UUID = Field(default_factory=uuid4)
    alert_id: UUID
    action: str = Field(..., description="Action taken (triggered, resolved, acknowledged, etc.)")
    details: Dict[str, Any] = Field(default_factory=dict)
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    user_id: Optional[str] = None


class NotificationTemplate(BaseModel):
    """Notification template for alerts."""
    
    id: UUID = Field(default_factory=uuid4)
    name: str = Field(..., min_length=1, max_length=255)
    channel: NotificationChannel
    subject_template: str = Field(..., description="Subject/title template")
    body_template: str = Field(..., description="Message body template")
    variables: Dict[str, str] = Field(default_factory=dict, description="Available template variables")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)