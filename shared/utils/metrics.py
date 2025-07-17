"""Metrics collection utilities for StreamFlow."""

import time
from contextlib import contextmanager
from typing import Dict, List, Optional
from collections import defaultdict, Counter
from datetime import datetime, timedelta

from prometheus_client import Counter as PrometheusCounter, Histogram, Gauge, generate_latest
from prometheus_client.registry import REGISTRY

from .config import get_settings
from .logging import get_logger

settings = get_settings()
logger = get_logger(__name__)


class MetricsCollector:
    """Centralized metrics collection."""
    
    def __init__(self):
        self.enabled = settings.metrics_enabled
        self._counters: Dict[str, PrometheusCounter] = {}
        self._histograms: Dict[str, Histogram] = {}
        self._gauges: Dict[str, Gauge] = {}
        self._custom_metrics = defaultdict(list)
        
        # Initialize common metrics
        self._init_common_metrics()
    
    def _init_common_metrics(self):
        """Initialize common application metrics."""
        if not self.enabled:
            return
            
        # HTTP Request metrics
        self.http_requests_total = PrometheusCounter(
            'http_requests_total',
            'Total HTTP requests',
            ['method', 'endpoint', 'status']
        )
        
        self.http_request_duration = Histogram(
            'http_request_duration_seconds',
            'HTTP request duration',
            ['method', 'endpoint']
        )
        
        # Event processing metrics
        self.events_processed_total = PrometheusCounter(
            'events_processed_total',
            'Total events processed',
            ['event_type', 'source']
        )
        
        self.event_processing_duration = Histogram(
            'event_processing_duration_seconds',
            'Event processing duration',
            ['event_type']
        )
        
        # Alert metrics
        self.alerts_triggered_total = PrometheusCounter(
            'alerts_triggered_total',
            'Total alerts triggered',
            ['severity', 'rule_name']
        )
        
        self.active_alerts = Gauge(
            'active_alerts',
            'Number of active alerts',
            ['severity']
        )
        
        # System metrics
        self.system_health = Gauge(
            'system_health',
            'System health status (1=healthy, 0=unhealthy)',
            ['service']
        )
        
        # Queue metrics
        self.queue_size = Gauge(
            'queue_size',
            'Message queue size',
            ['queue_name']
        )
        
        self.queue_processing_rate = Gauge(
            'queue_processing_rate',
            'Messages processed per second',
            ['queue_name']
        )
    
    def increment_counter(
        self, 
        name: str, 
        labels: Optional[Dict[str, str]] = None,
        value: float = 1.0
    ):
        """Increment a counter metric."""
        if not self.enabled:
            return
            
        try:
            if name not in self._counters:
                self._counters[name] = PrometheusCounter(
                    name,
                    f'Custom counter: {name}',
                    list(labels.keys()) if labels else []
                )
            
            if labels:
                self._counters[name].labels(**labels).inc(value)
            else:
                self._counters[name].inc(value)
                
        except Exception as e:
            logger.error(f"Failed to increment counter {name}: {e}")
    
    def set_gauge(
        self, 
        name: str, 
        value: float,
        labels: Optional[Dict[str, str]] = None
    ):
        """Set a gauge metric value."""
        if not self.enabled:
            return
            
        try:
            if name not in self._gauges:
                self._gauges[name] = Gauge(
                    name,
                    f'Custom gauge: {name}',
                    list(labels.keys()) if labels else []
                )
            
            if labels:
                self._gauges[name].labels(**labels).set(value)
            else:
                self._gauges[name].set(value)
                
        except Exception as e:
            logger.error(f"Failed to set gauge {name}: {e}")
    
    def observe_histogram(
        self, 
        name: str, 
        value: float,
        labels: Optional[Dict[str, str]] = None
    ):
        """Observe a histogram metric."""
        if not self.enabled:
            return
            
        try:
            if name not in self._histograms:
                self._histograms[name] = Histogram(
                    name,
                    f'Custom histogram: {name}',
                    list(labels.keys()) if labels else []
                )
            
            if labels:
                self._histograms[name].labels(**labels).observe(value)
            else:
                self._histograms[name].observe(value)
                
        except Exception as e:
            logger.error(f"Failed to observe histogram {name}: {e}")
    
    @contextmanager
    def timer(self, metric_name: str, labels: Optional[Dict[str, str]] = None):
        """Context manager for timing operations."""
        start_time = time.time()
        try:
            yield
        finally:
            duration = time.time() - start_time
            self.observe_histogram(f"{metric_name}_duration_seconds", duration, labels)
    
    def record_http_request(
        self, 
        method: str, 
        endpoint: str, 
        status_code: int, 
        duration: float
    ):
        """Record HTTP request metrics."""
        if not self.enabled:
            return
            
        self.http_requests_total.labels(
            method=method,
            endpoint=endpoint,
            status=str(status_code)
        ).inc()
        
        self.http_request_duration.labels(
            method=method,
            endpoint=endpoint
        ).observe(duration)
    
    def record_event_processed(
        self, 
        event_type: str, 
        source: str, 
        processing_time: float
    ):
        """Record event processing metrics."""
        if not self.enabled:
            return
            
        self.events_processed_total.labels(
            event_type=event_type,
            source=source
        ).inc()
        
        self.event_processing_duration.labels(
            event_type=event_type
        ).observe(processing_time)
    
    def record_alert_triggered(self, severity: str, rule_name: str):
        """Record alert triggered metric."""
        if not self.enabled:
            return
            
        self.alerts_triggered_total.labels(
            severity=severity,
            rule_name=rule_name
        ).inc()
    
    def update_active_alerts(self, severity: str, count: int):
        """Update active alerts gauge."""
        if not self.enabled:
            return
            
        self.active_alerts.labels(severity=severity).set(count)
    
    def update_system_health(self, service: str, healthy: bool):
        """Update system health status."""
        if not self.enabled:
            return
            
        self.system_health.labels(service=service).set(1 if healthy else 0)
    
    def update_queue_metrics(self, queue_name: str, size: int, processing_rate: float):
        """Update queue metrics."""
        if not self.enabled:
            return
            
        self.queue_size.labels(queue_name=queue_name).set(size)
        self.queue_processing_rate.labels(queue_name=queue_name).set(processing_rate)
    
    def get_metrics(self) -> str:
        """Get Prometheus metrics in text format."""
        if not self.enabled:
            return ""
            
        return generate_latest(REGISTRY).decode('utf-8')
    
    def add_custom_metric(self, name: str, value: float, labels: Optional[Dict[str, str]] = None):
        """Add a custom metric for later aggregation."""
        self._custom_metrics[name].append({
            'value': value,
            'labels': labels or {},
            'timestamp': datetime.utcnow()
        })
    
    def get_custom_metrics_summary(self, hours: int = 1) -> Dict[str, Dict]:
        """Get summary of custom metrics for the last N hours."""
        cutoff_time = datetime.utcnow() - timedelta(hours=hours)
        summary = {}
        
        for metric_name, values in self._custom_metrics.items():
            recent_values = [
                v for v in values 
                if v['timestamp'] >= cutoff_time
            ]
            
            if recent_values:
                numeric_values = [v['value'] for v in recent_values]
                summary[metric_name] = {
                    'count': len(numeric_values),
                    'sum': sum(numeric_values),
                    'avg': sum(numeric_values) / len(numeric_values),
                    'min': min(numeric_values),
                    'max': max(numeric_values)
                }
        
        return summary
    
    def clear_old_custom_metrics(self, hours: int = 24):
        """Clear custom metrics older than N hours."""
        cutoff_time = datetime.utcnow() - timedelta(hours=hours)
        
        for metric_name in self._custom_metrics:
            self._custom_metrics[metric_name] = [
                v for v in self._custom_metrics[metric_name]
                if v['timestamp'] >= cutoff_time
            ]


# Global metrics collector instance
metrics = MetricsCollector()


def get_metrics_collector() -> MetricsCollector:
    """Get the global metrics collector instance."""
    return metrics