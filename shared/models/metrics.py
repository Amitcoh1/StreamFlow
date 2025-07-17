"""Metrics models for StreamFlow."""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional
from uuid import UUID, uuid4

from pydantic import BaseModel, Field, validator


class MetricType(str, Enum):
    """Metric type enumeration."""
    COUNTER = "counter"
    GAUGE = "gauge"
    HISTOGRAM = "histogram"
    SUMMARY = "summary"


class AggregationType(str, Enum):
    """Aggregation type for metrics."""
    SUM = "sum"
    AVG = "avg"
    MIN = "min"
    MAX = "max"
    COUNT = "count"
    PERCENTILE_50 = "p50"
    PERCENTILE_90 = "p90"
    PERCENTILE_95 = "p95"
    PERCENTILE_99 = "p99"


class Metric(BaseModel):
    """Core metric model."""
    
    id: UUID = Field(default_factory=uuid4)
    name: str = Field(..., min_length=1, max_length=255)
    type: MetricType
    value: float
    labels: Dict[str, str] = Field(default_factory=dict)
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    source: str = Field(..., description="Metric source service")
    description: Optional[str] = None
    unit: Optional[str] = None
    
    @validator('name')
    def validate_name(cls, v):
        """Validate metric name format."""
        import re
        # Metric names should follow Prometheus naming conventions
        pattern = r'^[a-zA-Z_:][a-zA-Z0-9_:]*$'
        if not re.match(pattern, v):
            raise ValueError("Invalid metric name format")
        return v
    
    @validator('labels')
    def validate_labels(cls, v):
        """Validate metric labels."""
        for key, value in v.items():
            if not isinstance(key, str) or not isinstance(value, str):
                raise ValueError("Label keys and values must be strings")
        return v


class MetricAggregation(BaseModel):
    """Aggregated metric data."""
    
    metric_name: str
    aggregation_type: AggregationType
    value: float
    window_start: datetime
    window_end: datetime
    labels: Dict[str, str] = Field(default_factory=dict)
    sample_count: int = 0


class Dashboard(BaseModel):
    """Dashboard configuration."""
    
    id: UUID = Field(default_factory=uuid4)
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    widgets: List[Dict[str, Any]] = Field(default_factory=list)
    layout: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    created_by: str
    is_public: bool = False
    tags: List[str] = Field(default_factory=list)


class Widget(BaseModel):
    """Dashboard widget configuration."""
    
    id: UUID = Field(default_factory=uuid4)
    dashboard_id: UUID
    type: str = Field(..., description="Widget type (chart, table, single_stat, etc.)")
    title: str = Field(..., min_length=1, max_length=255)
    position: Dict[str, int] = Field(..., description="Widget position and size")
    query: str = Field(..., description="Metric query for the widget")
    options: Dict[str, Any] = Field(default_factory=dict)
    refresh_interval: int = Field(default=30, description="Refresh interval in seconds")


class TimeSeriesData(BaseModel):
    """Time series data point."""
    
    timestamp: datetime
    value: float
    labels: Dict[str, str] = Field(default_factory=dict)


class MetricQuery(BaseModel):
    """Metric query specification."""
    
    metric_name: str
    start_time: datetime
    end_time: datetime
    step: Optional[str] = None  # Time step for aggregation
    aggregation: Optional[AggregationType] = None
    filters: Dict[str, str] = Field(default_factory=dict)
    group_by: List[str] = Field(default_factory=list)


class MetricQueryResult(BaseModel):
    """Result of a metric query."""
    
    query: MetricQuery
    data: List[TimeSeriesData]
    total_points: int
    execution_time_ms: float
    cached: bool = False