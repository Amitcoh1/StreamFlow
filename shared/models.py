"""
Shared Pydantic models for StreamFlow
StreamFlow - real-time analytics pipeline

 
"""
from datetime import datetime
from typing import Any, Dict, List, Optional, Union
from enum import Enum
from uuid import UUID, uuid4
from pydantic import BaseModel, Field, field_validator


class EventType(str, Enum):
    """Event types"""
    WEB_CLICK = "web.click"
    WEB_PAGEVIEW = "web.pageview"
    API_REQUEST = "api.request"
    API_RESPONSE = "api.response"
    USER_LOGIN = "user.login"
    USER_LOGOUT = "user.logout"
    ERROR = "error"
    METRIC = "metric"
    CUSTOM = "custom"


class EventSeverity(str, Enum):
    """Event severity levels"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class Event(BaseModel):
    """Base event model"""
    id: UUID = Field(default_factory=uuid4)
    type: EventType
    source: str = Field(..., description="Source service or system")
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    severity: EventSeverity = Field(default=EventSeverity.MEDIUM)
    data: Dict[str, Any] = Field(default_factory=dict)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    correlation_id: Optional[str] = Field(default=None)
    session_id: Optional[str] = Field(default=None)
    user_id: Optional[str] = Field(default=None)
    tags: List[str] = Field(default_factory=list)
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat(),
            UUID: str
        }
    
    @field_validator("timestamp")
    @classmethod
    def validate_timestamp(cls, v):
        if isinstance(v, str):
            return datetime.fromisoformat(v.replace("Z", "+00:00"))
        return v


class AlertLevel(str, Enum):
    """Alert severity levels"""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class AlertChannel(str, Enum):
    """Alert notification channels"""
    EMAIL = "email"
    SLACK = "slack"
    WEBHOOK = "webhook"
    SMS = "sms"
    PUSH = "push"


class AlertRule(BaseModel):
    """Alert rule configuration"""
    id: UUID = Field(default_factory=uuid4)
    name: str
    description: Optional[str] = None
    condition: str = Field(..., description="Alert condition expression")
    threshold: float
    window: str = Field(..., description="Time window (e.g., '5m', '1h')")
    level: AlertLevel = Field(default=AlertLevel.WARNING)
    channels: List[AlertChannel] = Field(default_factory=list)
    enabled: bool = Field(default=True)
    suppression_minutes: int = Field(default=0)
    escalation_minutes: int = Field(default=0)
    tags: List[str] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    @field_validator("window")
    @classmethod
    def validate_window(cls, v):
        # Basic validation for time window format
        if not v.endswith(('s', 'm', 'h', 'd')):
            raise ValueError("Window must end with 's', 'm', 'h', or 'd'")
        try:
            int(v[:-1])
        except ValueError:
            raise ValueError("Window must start with a number")
        return v


class Alert(BaseModel):
    """Alert instance"""
    id: UUID = Field(default_factory=uuid4)
    rule_id: UUID
    level: AlertLevel
    title: str
    message: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    resolved: bool = Field(default=False)
    resolved_at: Optional[datetime] = None
    resolved_by: Optional[str] = None
    acknowledged: bool = Field(default=False)
    acknowledged_at: Optional[datetime] = None
    acknowledged_by: Optional[str] = None
    data: Dict[str, Any] = Field(default_factory=dict)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class MetricType(str, Enum):
    """Metric types"""
    COUNTER = "counter"
    GAUGE = "gauge"
    HISTOGRAM = "histogram"
    TIMER = "timer"


class MetricData(BaseModel):
    """Metric data point"""
    name: str
    type: MetricType
    value: float
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    tags: Dict[str, str] = Field(default_factory=dict)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class ProcessingStatus(str, Enum):
    """Processing status"""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    RETRYING = "retrying"
    CANCELLED = "cancelled"


class ProcessingResult(BaseModel):
    """Processing result"""
    id: UUID = Field(default_factory=uuid4)
    event_id: UUID
    status: ProcessingStatus
    started_at: datetime = Field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = None
    error: Optional[str] = None
    retry_count: int = Field(default=0)
    output: Optional[Dict[str, Any]] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class HealthStatus(str, Enum):
    """Health check status"""
    HEALTHY = "healthy"
    UNHEALTHY = "unhealthy"
    DEGRADED = "degraded"


class HealthCheck(BaseModel):
    """Health check response"""
    status: HealthStatus
    service: str
    version: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    checks: Dict[str, Any] = Field(default_factory=dict)
    uptime: Optional[float] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class PaginationParams(BaseModel):
    """Pagination parameters"""
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=100, ge=1, le=1000)
    sort_by: Optional[str] = None
    sort_order: str = Field(default="desc", pattern="^(asc|desc)$")


class PaginatedResponse(BaseModel):
    """Paginated response"""
    data: List[Any]
    pagination: Dict[str, Any]
    
    @classmethod
    def create(cls, data: List[Any], page: int, page_size: int, total: int):
        """Create paginated response"""
        return cls(
            data=data,
            pagination={
                "page": page,
                "page_size": page_size,
                "total": total,
                "pages": (total + page_size - 1) // page_size,
                "has_next": page * page_size < total,
                "has_prev": page > 1
            }
        )


class ErrorResponse(BaseModel):
    """Error response model"""
    error: str
    message: str
    details: Optional[Dict[str, Any]] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    correlation_id: Optional[str] = None


class APIResponse(BaseModel):
    """Generic API response"""
    success: bool
    message: str
    data: Optional[Any] = None
    error: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    correlation_id: Optional[str] = None


# Message models for RabbitMQ
class MessageEnvelope(BaseModel):
    """Message envelope for RabbitMQ"""
    routing_key: str
    payload: Dict[str, Any]
    headers: Dict[str, Any] = Field(default_factory=dict)
    correlation_id: Optional[str] = None
    reply_to: Optional[str] = None
    expiration: Optional[int] = None
    priority: int = Field(default=0)
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class TaskMessage(BaseModel):
    """Task message for background processing"""
    task_id: UUID = Field(default_factory=uuid4)
    task_type: str
    payload: Dict[str, Any]
    retry_count: int = Field(default=0)
    max_retries: int = Field(default=3)
    delay: Optional[int] = None
    eta: Optional[datetime] = None
    expires: Optional[datetime] = None
    priority: int = Field(default=0)
    correlation_id: Optional[str] = None
