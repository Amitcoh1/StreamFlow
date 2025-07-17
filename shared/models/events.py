"""Event models for StreamFlow."""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, Optional
from uuid import UUID, uuid4

from pydantic import BaseModel, Field, validator


class EventType(str, Enum):
    """Event type enumeration."""
    USER_CLICK = "user.click"
    USER_VIEW = "user.view"
    USER_LOGIN = "user.login"
    USER_LOGOUT = "user.logout"
    SYSTEM_ERROR = "system.error"
    SYSTEM_WARNING = "system.warning"
    SYSTEM_INFO = "system.info"
    API_REQUEST = "api.request"
    API_RESPONSE = "api.response"
    CUSTOM = "custom"


class Event(BaseModel):
    """Core event model."""
    
    id: UUID = Field(default_factory=uuid4)
    type: EventType
    source: str = Field(..., description="Event source identifier")
    data: Dict[str, Any] = Field(default_factory=dict)
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    tags: Dict[str, str] = Field(default_factory=dict)
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat(),
            UUID: str
        }
    
    @validator('data')
    def validate_data(cls, v):
        """Validate event data."""
        if not isinstance(v, dict):
            raise ValueError("Event data must be a dictionary")
        return v
    
    @validator('timestamp')
    def validate_timestamp(cls, v):
        """Validate timestamp is not in the future."""
        if v > datetime.utcnow():
            raise ValueError("Event timestamp cannot be in the future")
        return v


class EventBatch(BaseModel):
    """Batch of events for efficient processing."""
    
    events: list[Event]
    batch_id: UUID = Field(default_factory=uuid4)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    @validator('events')
    def validate_events(cls, v):
        """Validate events list."""
        if not v:
            raise ValueError("Event batch cannot be empty")
        if len(v) > 1000:
            raise ValueError("Event batch cannot contain more than 1000 events")
        return v


class ProcessedEvent(Event):
    """Event after processing with analytics data."""
    
    processed_at: datetime = Field(default_factory=datetime.utcnow)
    processing_duration_ms: float = 0.0
    analytics_data: Dict[str, Any] = Field(default_factory=dict)
    enriched_data: Dict[str, Any] = Field(default_factory=dict)