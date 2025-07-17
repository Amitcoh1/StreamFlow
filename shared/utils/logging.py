"""Logging utilities for StreamFlow."""

import logging
import sys
from datetime import datetime
from typing import Any, Dict, Optional

import structlog
from pythonjsonlogger import jsonlogger

from .config import get_settings

settings = get_settings()


def setup_logging() -> None:
    """Setup structured logging for the application."""
    # Configure structlog
    structlog.configure(
        processors=[
            structlog.stdlib.filter_by_level,
            structlog.stdlib.add_logger_name,
            structlog.stdlib.add_log_level,
            structlog.stdlib.PositionalArgumentsFormatter(),
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.UnicodeDecoder(),
            structlog.processors.JSONRenderer()
        ],
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )

    # Configure standard logging
    if settings.log_format.lower() == "json":
        formatter = jsonlogger.JsonFormatter(
            "%(asctime)s %(name)s %(levelname)s %(message)s"
        )
    else:
        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )

    # Configure handlers
    handlers = [logging.StreamHandler(sys.stdout)]
    
    if settings.log_file:
        handlers.append(logging.FileHandler(settings.log_file))

    # Configure root logger
    logging.basicConfig(
        level=getattr(logging, settings.log_level.upper()),
        handlers=handlers,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )

    # Set handler formatters
    for handler in logging.root.handlers:
        handler.setFormatter(formatter)


def get_logger(name: str) -> structlog.BoundLogger:
    """Get a structured logger instance."""
    return structlog.get_logger(name)


class LoggingMiddleware:
    """Logging middleware for FastAPI."""
    
    def __init__(self, app):
        self.app = app
        self.logger = get_logger("middleware.logging")
    
    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return
        
        start_time = datetime.utcnow()
        
        async def send_wrapper(message):
            if message["type"] == "http.response.start":
                self.logger.info(
                    "Request completed",
                    method=scope["method"],
                    path=scope["path"],
                    status_code=message["status"],
                    duration_ms=(datetime.utcnow() - start_time).total_seconds() * 1000,
                    user_agent=dict(scope.get("headers", {})).get(b"user-agent", b"").decode(),
                    remote_addr=scope.get("client", ["unknown"])[0]
                )
            await send(message)
        
        await self.app(scope, receive, send_wrapper)


def log_function_call(func_name: str, **kwargs) -> None:
    """Log function call with parameters."""
    logger = get_logger("function_calls")
    logger.info(f"Function called: {func_name}", **kwargs)


def log_error(error: Exception, context: Optional[Dict[str, Any]] = None) -> None:
    """Log error with context."""
    logger = get_logger("errors")
    logger.error(
        "Error occurred",
        error_type=type(error).__name__,
        error_message=str(error),
        context=context or {}
    )


def log_metric(metric_name: str, value: float, labels: Optional[Dict[str, str]] = None) -> None:
    """Log metric for monitoring."""
    logger = get_logger("metrics")
    logger.info(
        "Metric recorded",
        metric_name=metric_name,
        value=value,
        labels=labels or {},
        timestamp=datetime.utcnow().isoformat()
    )


def log_event(event_type: str, data: Dict[str, Any]) -> None:
    """Log application event."""
    logger = get_logger("events")
    logger.info(
        "Event occurred",
        event_type=event_type,
        **data
    )


def log_performance(operation: str, duration_ms: float, **kwargs) -> None:
    """Log performance metrics."""
    logger = get_logger("performance")
    logger.info(
        "Performance metric",
        operation=operation,
        duration_ms=duration_ms,
        **kwargs
    )


def log_security_event(event_type: str, user_id: Optional[str] = None, **kwargs) -> None:
    """Log security-related events."""
    logger = get_logger("security")
    logger.warning(
        "Security event",
        event_type=event_type,
        user_id=user_id,
        **kwargs
    )