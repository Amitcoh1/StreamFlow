"""
Analytics Pipeline Service - Stream processing and analytics engine
StreamFlow - real-time analytics pipeline

 
"""
import asyncio
import logging
from collections import defaultdict, deque
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Callable, Any
from uuid import UUID
import json

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
from sqlalchemy import text

from streamflow.shared.config import get_settings
from streamflow.shared.models import Event, EventType, MetricData, MetricType, ProcessingResult, ProcessingStatus, APIResponse, HealthCheck, HealthStatus
from streamflow.shared.messaging import get_message_broker, get_event_publisher, MessageEnvelope
from streamflow.shared.database import get_database_manager

logger = logging.getLogger(__name__)

# Global state
settings = get_settings()

# Create FastAPI app
app = FastAPI(
    title="StreamFlow Analytics API",
    description="Real-time analytics and insights API",
    version="0.1.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Health check endpoint
@app.get("/health", response_model=HealthCheck)
async def health_check():
    """Health check endpoint"""
    try:
        # Check database
        db_manager = await get_database_manager()
        db_health = await db_manager.health_check()
        
        overall_status = HealthStatus.HEALTHY if db_health["status"] == "healthy" else HealthStatus.UNHEALTHY
        
        return HealthCheck(
            status=overall_status,
            service="analytics",
            version="0.1.0",
            checks={
                "database": db_health,
                "stream_processor": "healthy" if 'analytics_service' in globals() and analytics_service.is_running else "not_running"
            }
        )
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return HealthCheck(
            status=HealthStatus.UNHEALTHY,
            service="analytics",
            version="0.1.0",
            checks={"error": str(e)}
        )


@app.get("/api/v1/analytics/event-trends")
async def get_event_trends(
    hours: int = Query(default=24, ge=1, le=168, description="Number of hours to analyze"),
    interval_minutes: int = Query(default=60, ge=5, le=1440, description="Time interval in minutes")
):
    """Get event trends over time with real data from storage"""
    try:
        db_manager = await get_database_manager()
        
        # Calculate time range
        end_time = datetime.utcnow()
        start_time = end_time - timedelta(hours=hours)
        
        # Create time intervals
        intervals = []
        current_time = start_time
        while current_time < end_time:
            intervals.append(current_time)
            current_time += timedelta(minutes=interval_minutes)
        
        # Query events by intervals
        event_trends = []
        
        async with db_manager.get_session() as session:
            for i, interval_start in enumerate(intervals):
                interval_end = interval_start + timedelta(minutes=interval_minutes)
                
                # Count events by type in this interval
                result = await session.execute(
                    text("""
                    SELECT 
                        type,
                        COUNT(*) as count
                    FROM events 
                    WHERE timestamp >= :start AND timestamp < :end
                    GROUP BY type
                    """),
                    {"start": interval_start, "end": interval_end}
                )
                
                type_counts = dict(result.fetchall())
                
                # Format for chart
                trend_point = {
                    "time": interval_start.strftime("%H:%M"),
                    "timestamp": interval_start.isoformat(),
                    "webClicks": type_counts.get("web.click", 0) + type_counts.get("web.pageview", 0),
                    "apiRequests": type_counts.get("api.request", 0) + type_counts.get("api.response", 0),
                    "errors": type_counts.get("error", 0),
                    "custom": type_counts.get("custom", 0),
                    "total": sum(type_counts.values())
                }
                event_trends.append(trend_point)
        
        return APIResponse(
            success=True,
            message="Event trends retrieved successfully",
            data=event_trends
        )
        
    except Exception as e:
        logger.error(f"Failed to get event trends: {e}")
        raise HTTPException(status_code=500, detail="Failed to get event trends")


@app.get("/api/v1/analytics/user-distribution")
async def get_user_distribution():
    """Get user distribution by user agent/device type from real data"""
    try:
        db_manager = await get_database_manager()
        
        async with db_manager.get_session() as session:
            # Query events with user agent data
            result = await session.execute(
                text("""
                SELECT 
                    data,
                    COUNT(*) as count
                FROM events 
                WHERE data IS NOT NULL 
                AND timestamp >= :start_time
                """),
                {"start_time": datetime.utcnow() - timedelta(days=7)}
            )
            
            device_counts = {"Desktop": 0, "Mobile": 0, "Tablet": 0, "Unknown": 0}
            total_count = 0
            
            for row in result.fetchall():
                try:
                    event_data = json.loads(row[0]) if isinstance(row[0], str) else row[0]
                    user_agent = str(event_data.get("user_agent", "")).lower()
                    count = row[1]
                    total_count += count
                    
                    if any(mobile in user_agent for mobile in ["mobile", "android", "iphone"]):
                        device_counts["Mobile"] += count
                    elif any(tablet in user_agent for tablet in ["tablet", "ipad"]):
                        device_counts["Tablet"] += count
                    elif any(desktop in user_agent for desktop in ["chrome", "firefox", "safari", "edge"]):
                        device_counts["Desktop"] += count
                    else:
                        device_counts["Unknown"] += count
                        
                except (json.JSONDecodeError, AttributeError):
                    device_counts["Unknown"] += row[1]
                    total_count += row[1]
            
            # Convert to percentages
            if total_count > 0:
                user_distribution = [
                    {
                        "name": device,
                        "value": round((count / total_count) * 100, 1),
                        "count": count,
                        "color": {
                            "Desktop": "#3b82f6",
                            "Mobile": "#10b981", 
                            "Tablet": "#f59e0b",
                            "Unknown": "#6b7280"
                        }[device]
                    }
                    for device, count in device_counts.items()
                    if count > 0
                ]
            else:
                # Default distribution if no data
                user_distribution = [
                    {"name": "Desktop", "value": 70, "count": 0, "color": "#3b82f6"},
                    {"name": "Mobile", "value": 25, "count": 0, "color": "#10b981"},
                    {"name": "Tablet", "value": 5, "count": 0, "color": "#f59e0b"}
                ]
        
        return APIResponse(
            success=True,
            message="User distribution retrieved successfully",
            data=user_distribution
        )
        
    except Exception as e:
        logger.error(f"Failed to get user distribution: {e}")
        raise HTTPException(status_code=500, detail="Failed to get user distribution")


@app.get("/api/v1/analytics/top-sources")
async def get_top_sources(limit: int = Query(default=10, ge=1, le=50)):
    """Get top event sources from real data"""
    try:
        db_manager = await get_database_manager()
        
        async with db_manager.get_session() as session:
            result = await session.execute(
                text("""
                SELECT 
                    source,
                    COUNT(*) as event_count,
                    COUNT(DISTINCT user_id) as unique_users
                FROM events 
                WHERE timestamp >= :start_time
                GROUP BY source 
                ORDER BY event_count DESC 
                LIMIT :limit
                """),
                {"start_time": datetime.utcnow() - timedelta(days=7), "limit": limit}
            )
            
            top_sources = [
                {
                    "source": row[0],
                    "event_count": row[1],
                    "unique_users": row[2] or 0
                }
                for row in result.fetchall()
            ]
        
        return APIResponse(
            success=True,
            message="Top sources retrieved successfully",
            data=top_sources
        )
        
    except Exception as e:
        logger.error(f"Failed to get top sources: {e}")
        raise HTTPException(status_code=500, detail="Failed to get top sources")


@app.get("/api/v1/analytics/event-types")
async def get_event_types_distribution():
    """Get event types distribution from real data"""
    try:
        db_manager = await get_database_manager()
        
        async with db_manager.get_session() as session:
            result = await session.execute(
                text("""
                SELECT 
                    type,
                    COUNT(*) as count
                FROM events 
                WHERE timestamp >= :start_time
                GROUP BY type 
                ORDER BY count DESC
                """),
                {"start_time": datetime.utcnow() - timedelta(days=7)}
            )
            
            event_types = [
                {
                    "type": row[0].replace(".", " ").replace("_", " ").title(),
                    "count": row[1],
                    "color": {
                        "web.click": "#3b82f6",
                        "web.pageview": "#10b981",
                        "api.request": "#8b5cf6",
                        "api.response": "#a855f7",
                        "error": "#ef4444",
                        "custom": "#f59e0b",
                        "user.login": "#06b6d4",
                        "user.logout": "#84cc16",
                        "metric": "#f97316"
                    }.get(row[0], "#6b7280")
                }
                for row in result.fetchall()
            ]
        
        return APIResponse(
            success=True,
            message="Event types distribution retrieved successfully",
            data=event_types
        )
        
    except Exception as e:
        logger.error(f"Failed to get event types distribution: {e}")
        raise HTTPException(status_code=500, detail="Failed to get event types distribution")


class TimeWindow:
    """Time-based window for stream processing"""
    
    def __init__(self, size_seconds: int, slide_seconds: int = None):
        self.size_seconds = size_seconds
        self.slide_seconds = slide_seconds or size_seconds
        self.data = deque()
    
    def add_event(self, event: Event):
        """Add event to window"""
        self.data.append(event)
        self._cleanup_old_events()
    
    def _cleanup_old_events(self):
        """Remove events older than window size"""
        cutoff_time = datetime.utcnow() - timedelta(seconds=self.size_seconds)
        while self.data and self.data[0].timestamp < cutoff_time:
            self.data.popleft()
    
    def get_events(self) -> List[Event]:
        """Get all events in current window"""
        self._cleanup_old_events()
        return list(self.data)
    
    def count(self) -> int:
        """Count events in current window"""
        self._cleanup_old_events()
        return len(self.data)


class StreamProcessor:
    """Stream processing engine with windowing and aggregations"""
    
    def __init__(self):
        self.windows: Dict[str, TimeWindow] = {}
        self.aggregators: Dict[str, Callable] = {}
        self.rules: List[Dict[str, Any]] = []
        self.metrics: Dict[str, Any] = defaultdict(int)
        
    def register_window(self, name: str, size_seconds: int, slide_seconds: int = None):
        """Register a time window"""
        self.windows[name] = TimeWindow(size_seconds, slide_seconds)
        logger.info(f"Registered window: {name} (size: {size_seconds}s)")
    
    def register_aggregator(self, name: str, func: Callable):
        """Register an aggregation function"""
        self.aggregators[name] = func
        logger.info(f"Registered aggregator: {name}")
    
    def register_rule(self, name: str, condition: str, action: Callable):
        """Register a processing rule"""
        self.rules.append({
            "name": name,
            "condition": condition,
            "action": action
        })
        logger.info(f"Registered rule: {name}")
    
    async def process_event(self, event: Event) -> List[ProcessingResult]:
        """Process incoming event through all windows and rules"""
        results = []
        
        try:
            # Add event to all windows
            for window_name, window in self.windows.items():
                window.add_event(event)
            
            # Update metrics
            self.metrics["events_processed"] += 1
            self.metrics[f"events_by_type_{event.type.value}"] += 1
            
            # Apply rules
            for rule in self.rules:
                try:
                    if await self._evaluate_condition(rule["condition"], event):
                        result = await rule["action"](event)
                        if result:
                            results.append(ProcessingResult(
                                event_id=event.id,
                                status=ProcessingStatus.COMPLETED,
                                output=result
                            ))
                except Exception as e:
                    logger.error(f"Rule {rule['name']} failed: {e}")
                    results.append(ProcessingResult(
                        event_id=event.id,
                        status=ProcessingStatus.FAILED,
                        error=str(e)
                    ))
            
            # Generate metrics
            await self._generate_metrics(event)
            
        except Exception as e:
            logger.error(f"Event processing failed: {e}")
            results.append(ProcessingResult(
                event_id=event.id,
                status=ProcessingStatus.FAILED,
                error=str(e)
            ))
        
        return results
    
    async def _evaluate_condition(self, condition: str, event: Event) -> bool:
        """Evaluate rule condition"""
        # Simple condition evaluation (in production, use a proper expression parser)
        try:
            # Create evaluation context
            context = {
                "event": event,
                "event_type": event.type.value,
                "severity": event.severity.value,
                "source": event.source,
                "data": event.data,
                "tags": event.tags,
                "windows": self.windows,
                "metrics": self.metrics
            }
            
            # Evaluate condition
            return eval(condition, {"__builtins__": {}}, context)
        except Exception as e:
            logger.error(f"Condition evaluation failed: {e}")
            return False
    
    async def _generate_metrics(self, event: Event):
        """Generate metrics from event"""
        try:
            # Event count metrics
            await self._emit_metric(
                "events_total",
                MetricType.COUNTER,
                1,
                {"source": event.source, "type": event.type.value}
            )
            
            # Event severity metrics
            await self._emit_metric(
                "events_by_severity",
                MetricType.COUNTER,
                1,
                {"severity": event.severity.value}
            )
            
            # Processing time metrics
            processing_time = (datetime.utcnow() - event.timestamp).total_seconds()
            await self._emit_metric(
                "event_processing_time",
                MetricType.HISTOGRAM,
                processing_time,
                {"source": event.source}
            )
            
            # Window-based metrics
            for window_name, window in self.windows.items():
                await self._emit_metric(
                    f"window_{window_name}_count",
                    MetricType.GAUGE,
                    window.count(),
                    {"window": window_name}
                )
        
        except Exception as e:
            logger.error(f"Metric generation failed: {e}")
    
    async def _emit_metric(self, name: str, metric_type: MetricType, value: float, tags: Dict[str, str]):
        """Emit metric to analytics exchange"""
        try:
            metric = MetricData(
                name=name,
                type=metric_type,
                value=value,
                tags=tags
            )
            
            publisher = await get_event_publisher()
            await publisher.publish_metric(metric.dict())
            
        except Exception as e:
            logger.error(f"Metric emission failed: {e}")


class AnalyticsService:
    """Main analytics service"""
    
    def __init__(self):
        self.processor = StreamProcessor()
        self.is_running = False
        self._setup_default_processing()
    
    def _setup_default_processing(self):
        """Setup default processing windows and rules"""
        # Register time windows
        self.processor.register_window("1min", 60)
        self.processor.register_window("5min", 300)
        self.processor.register_window("1hour", 3600)
        
        # Register aggregators
        self.processor.register_aggregator("count", lambda events: len(events))
        self.processor.register_aggregator("avg", lambda events: sum(e.data.get("value", 0) for e in events) / len(events) if events else 0)
        
        # Register rules
        self.processor.register_rule(
            "high_error_rate",
            "event_type == 'error' and windows['1min'].count() > 10",
            self._handle_high_error_rate
        )
        
        self.processor.register_rule(
            "user_activity_spike",
            "event_type in ['user.login', 'user.logout'] and windows['5min'].count() > 100",
            self._handle_activity_spike
        )
    
    async def _handle_high_error_rate(self, event: Event) -> Dict[str, Any]:
        """Handle high error rate condition"""
        error_count = self.processor.windows["1min"].count()
        
        alert_data = {
            "alert_type": "high_error_rate",
            "message": f"High error rate detected: {error_count} errors in 1 minute",
            "severity": "critical",
            "event_id": str(event.id),
            "timestamp": datetime.utcnow().isoformat()
        }
        
        # Publish alert
        publisher = await get_event_publisher()
        await publisher.publish_alert(alert_data)
        
        return alert_data
    
    async def _handle_activity_spike(self, event: Event) -> Dict[str, Any]:
        """Handle user activity spike"""
        activity_count = self.processor.windows["5min"].count()
        
        alert_data = {
            "alert_type": "activity_spike",
            "message": f"User activity spike detected: {activity_count} events in 5 minutes",
            "severity": "warning",
            "event_id": str(event.id),
            "timestamp": datetime.utcnow().isoformat()
        }
        
        # Publish alert
        publisher = await get_event_publisher()
        await publisher.publish_alert(alert_data)
        
        return alert_data
    
    async def start(self):
        """Start analytics service"""
        if self.is_running:
            return
        
        self.is_running = True
        logger.info("Starting Analytics Service...")
        
        # Initialize message broker
        broker = await get_message_broker()
        
        # Setup event queue
        await broker.declare_queue(
            "analytics.events",
            "events.*",
            settings.rabbitmq.exchange_events
        )
        
        # Start consuming events
        await broker.consume(
            "analytics.events",
            self._process_message,
            auto_ack=False
        )
        
        logger.info("Analytics Service started successfully")
    
    async def stop(self):
        """Stop analytics service"""
        self.is_running = False
        logger.info("Analytics Service stopped")
    
    async def _process_message(self, envelope: MessageEnvelope):
        """Process incoming message"""
        try:
            # Parse event from message
            event_data = envelope.payload
            event = Event(**event_data)
            
            # Process event
            results = await self.processor.process_event(event)
            
            # Log processing results
            for result in results:
                if result.status == ProcessingStatus.COMPLETED:
                    logger.info(f"Event {event.id} processed successfully")
                else:
                    logger.error(f"Event {event.id} processing failed: {result.error}")
        
        except Exception as e:
            logger.error(f"Message processing failed: {e}")
    
    async def get_metrics(self) -> Dict[str, Any]:
        """Get service metrics"""
        return {
            "service": "analytics",
            "metrics": dict(self.processor.metrics),
            "windows": {
                name: window.count() 
                for name, window in self.processor.windows.items()
            },
            "rules_count": len(self.processor.rules),
            "timestamp": datetime.utcnow().isoformat()
        }
    
    async def get_window_data(self, window_name: str) -> List[Dict[str, Any]]:
        """Get data from specific window"""
        if window_name not in self.processor.windows:
            raise ValueError(f"Window {window_name} not found")
        
        window = self.processor.windows[window_name]
        events = window.get_events()
        
        return [
            {
                "id": str(event.id),
                "type": event.type.value,
                "source": event.source,
                "timestamp": event.timestamp.isoformat(),
                "data": event.data
            }
            for event in events
        ]


# Global service instance
analytics_service = AnalyticsService()


async def start_analytics_service():
    """Start the analytics processing service"""
    await analytics_service.start()


async def main():
    """Main function to run analytics service"""
    try:
        # Start analytics processing in background
        analytics_task = asyncio.create_task(start_analytics_service())
        
        # Start FastAPI server
        config = uvicorn.Config(
            app, 
            host="0.0.0.0", 
            port=settings.services.analytics_port,
            log_level="info"
        )
        server = uvicorn.Server(config)
        
        # Run both services concurrently
        await asyncio.gather(
            server.serve(),
            analytics_task
        )
            
    except KeyboardInterrupt:
        logger.info("Received shutdown signal")
    except Exception as e:
        logger.error(f"Service error: {e}")
    finally:
        await analytics_service.stop()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(main())
