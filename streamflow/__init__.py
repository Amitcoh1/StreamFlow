"""
StreamFlow - Enterprise-Grade Real-Time Analytics Pipeline

A high-performance, scalable real-time analytics platform built with Python, FastAPI, and RabbitMQ.
Designed for enterprise use cases requiring real-time data processing, monitoring, and alerting.

Features:
- Real-time event ingestion and processing
- Advanced analytics and aggregations
- Intelligent alerting system
- Interactive React dashboard
- Distributed architecture with microservices
- High availability and fault tolerance
- Comprehensive monitoring and observability
"""

__version__ = "1.0.0"
__author__ = "Amit Cohen"
__email__ = "amit.cohen@streamflow.dev"
__description__ = "real-time analytics pipeline using Python, FastAPI, and RabbitMQ"

# Core imports
from .shared.models import Event, AlertRule, MetricData
from .shared.config import Settings
from .shared.messaging import MessageBroker
from .shared.database import DatabaseManager

__all__ = [
    "Event",
    "AlertRule", 
    "MetricData",
    "Settings",
    "MessageBroker",
    "DatabaseManager",
    "__version__",
    "__author__",
    "__email__",
    "__description__"
]