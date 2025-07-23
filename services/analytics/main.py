"""
Analytics Pipeline Service - Stream processing and analytics engine with FastAPI endpoints
StreamFlow - real-time analytics pipeline

 
"""
import asyncio
import logging
from collections import defaultdict, deque
from contextlib import asynccontextmanager
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Callable, Any, Union
from uuid import UUID
import json

from fastapi import FastAPI, HTTPException, Depends, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
import uvicorn
import sqlalchemy as sa
from sqlalchemy import func, text

from streamflow.shared.config import get_settings
from streamflow.shared.models import (
    Event, EventType, MetricData, MetricType, ProcessingResult, ProcessingStatus,
    HealthCheck, HealthStatus, APIResponse
)
from streamflow.shared.messaging import get_message_broker, get_event_publisher, MessageEnvelope
from streamflow.shared.database import get_database_manager

logger = logging.getLogger(__name__)

# Global state
settings = get_settings()
security = HTTPBearer()


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
            await publisher.publish_metric(metric.model_dump())
            
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


async def authenticate_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Authenticate user"""
    if not credentials.credentials:
        raise HTTPException(status_code=401, detail="Invalid authentication credentials")
    return {"user_id": "authenticated_user"}


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events"""
    # Startup
    logger.info("Starting Analytics API Service...")
    
    # Initialize database
    db_manager = await get_database_manager()
    await db_manager.create_tables()
    
    # Start analytics service in background
    asyncio.create_task(analytics_service.start())
    
    logger.info("Analytics API Service started successfully")
    
    yield
    
    # Shutdown
    logger.info("Shutting down Analytics API Service...")
    await analytics_service.stop()
    await db_manager.close()
    logger.info("Analytics API Service stopped")


# Create FastAPI app
app = FastAPI(
    title="StreamFlow Analytics API",
    description="Real-time analytics and stream processing API",
    version="0.1.0",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Health check endpoints
@app.get("/health", response_model=HealthCheck)
async def health_check():
    """Health check endpoint"""
    try:
        # Check database
        db_manager = await get_database_manager()
        db_health = await db_manager.health_check()
        
        # Check message broker
        broker = await get_message_broker()
        broker_health = {"status": "healthy" if broker.is_connected else "unhealthy"}
        
        overall_status = HealthStatus.HEALTHY
        if db_health["status"] != "healthy" or broker_health["status"] != "healthy":
            overall_status = HealthStatus.UNHEALTHY
        
        return HealthCheck(
            status=overall_status,
            service="analytics",
            version="0.1.0",
            checks={
                "database": db_health,
                "message_broker": broker_health,
                "analytics_service": "running" if analytics_service.is_running else "stopped"
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


@app.get("/ready")
async def readiness_check():
    """Readiness check endpoint"""
    return {"status": "ready", "service": "analytics"}


# Analytics endpoints
@app.get("/api/v1/analytics/event-trends")
async def get_event_trends(
    hours: int = Query(default=24, ge=1, le=168),
    interval_minutes: int = Query(default=60, ge=5, le=1440),
    user=Depends(authenticate_user)
):
    """Get event trends over time with real data from database"""
    
    try:
        db_manager = await get_database_manager()
        end_time = datetime.utcnow()
        start_time = end_time - timedelta(hours=hours)
        
        # Create time buckets based on interval
        bucket_size = f"{interval_minutes} minutes"
        
        # Query database for event trends
        async with db_manager.get_session() as session:
            query = text("""
                SELECT 
                    DATE_TRUNC('hour', timestamp) + 
                    INTERVAL '1 hour' * FLOOR(EXTRACT(minute FROM timestamp) / :interval) AS time_bucket,
                    COUNT(*) as event_count,
                    COUNT(DISTINCT user_id) as unique_users
                FROM events 
                WHERE timestamp >= :start_time AND timestamp <= :end_time
                GROUP BY time_bucket
                ORDER BY time_bucket
            """)
            
            result = await session.execute(query, {
                "start_time": start_time,
                "end_time": end_time,
                "interval": interval_minutes
            })
            
            trends = []
            for row in result:
                trends.append({
                    "time": row.time_bucket.isoformat(),
                    "events": row.event_count,
                    "users": row.unique_users
                })
        
        return APIResponse(
            success=True,
            message="Event trends retrieved successfully",
            data=trends
        )
    except Exception as e:
        logger.error(f"Failed to get event trends: {e}")
        raise HTTPException(status_code=500, detail="Failed to get event trends")


@app.get("/api/v1/analytics/user-distribution")
async def get_user_distribution(user=Depends(authenticate_user)):
    """Get user distribution by device type from real user-agent data"""
    
    try:
        db_manager = await get_database_manager()
        
        async with db_manager.get_session() as session:
            # Extract device info from user-agent data
            query = text("""
                SELECT 
                    CASE 
                        WHEN data->>'user_agent' ILIKE '%mobile%' OR data->>'user_agent' ILIKE '%android%' 
                             OR data->>'user_agent' ILIKE '%iphone%' THEN 'Mobile'
                        WHEN data->>'user_agent' ILIKE '%tablet%' OR data->>'user_agent' ILIKE '%ipad%' THEN 'Tablet'
                        WHEN data->>'user_agent' ILIKE '%bot%' OR data->>'user_agent' ILIKE '%crawler%' THEN 'Bot'
                        ELSE 'Desktop'
                    END as device_type,
                    COUNT(DISTINCT user_id) as user_count,
                    COUNT(*) as event_count
                FROM events 
                WHERE data->>'user_agent' IS NOT NULL
                    AND timestamp >= NOW() - INTERVAL '7 days'
                GROUP BY device_type
                ORDER BY user_count DESC
            """)
            
            result = await session.execute(query)
            
            distribution = []
            total_users = 0
            
            for row in result:
                distribution.append({
                    "name": row.device_type,
                    "users": row.user_count,
                    "events": row.event_count
                })
                total_users += row.user_count
            
            # Calculate percentages
            for item in distribution:
                item["percentage"] = round((item["users"] / total_users * 100), 1) if total_users > 0 else 0
        
        return APIResponse(
            success=True,
            message="User distribution retrieved successfully",
            data=distribution
        )
    except Exception as e:
        logger.error(f"Failed to get user distribution: {e}")
        raise HTTPException(status_code=500, detail="Failed to get user distribution")


@app.get("/api/v1/analytics/top-sources")
async def get_top_sources(
    limit: int = Query(default=10, ge=1, le=50),
    user=Depends(authenticate_user)
):
    """Get top event sources with user counts and activity metrics"""
    
    try:
        db_manager = await get_database_manager()
        
        async with db_manager.get_session() as session:
            query = text("""
                SELECT 
                    source,
                    COUNT(*) as event_count,
                    COUNT(DISTINCT user_id) as unique_users,
                    AVG(EXTRACT(epoch FROM (NOW() - timestamp))) as avg_age_seconds,
                    MAX(timestamp) as last_seen
                FROM events 
                WHERE timestamp >= NOW() - INTERVAL '24 hours'
                GROUP BY source
                ORDER BY event_count DESC
                LIMIT :limit
            """)
            
            result = await session.execute(query, {"limit": limit})
            
            sources = []
            for row in result:
                sources.append({
                    "source": row.source,
                    "event_count": row.event_count,
                    "unique_users": row.unique_users,
                    "avg_age_hours": round(row.avg_age_seconds / 3600, 1) if row.avg_age_seconds else 0,
                    "last_seen": row.last_seen.isoformat() if row.last_seen else None
                })
        
        return APIResponse(
            success=True,
            message="Top sources retrieved successfully",
            data=sources
        )
    except Exception as e:
        logger.error(f"Failed to get top sources: {e}")
        raise HTTPException(status_code=500, detail="Failed to get top sources")


@app.get("/api/v1/analytics/event-types")
async def get_event_types(user=Depends(authenticate_user)):
    """Get event type distribution with real data"""
    
    try:
        db_manager = await get_database_manager()
        
        async with db_manager.get_session() as session:
            query = text("""
                SELECT 
                    type,
                    COUNT(*) as count,
                    COUNT(DISTINCT user_id) as unique_users,
                    COUNT(DISTINCT source) as unique_sources,
                    AVG(
                        CASE 
                            WHEN data->>'processing_time' IS NOT NULL 
                            THEN (data->>'processing_time')::float 
                            ELSE NULL 
                        END
                    ) as avg_processing_time
                FROM events 
                WHERE timestamp >= NOW() - INTERVAL '24 hours'
                GROUP BY type
                ORDER BY count DESC
            """)
            
            result = await session.execute(query)
            
            event_types = []
            total_events = 0
            
            for row in result:
                event_types.append({
                    "name": row.type,
                    "count": row.count,
                    "unique_users": row.unique_users,
                    "unique_sources": row.unique_sources,
                    "avg_processing_time": round(row.avg_processing_time, 3) if row.avg_processing_time else None
                })
                total_events += row.count
            
            # Calculate percentages
            for item in event_types:
                item["percentage"] = round((item["count"] / total_events * 100), 1) if total_events > 0 else 0
        
        return APIResponse(
            success=True,
            message="Event types retrieved successfully",
            data=event_types
        )
    except Exception as e:
        logger.error(f"Failed to get event types: {e}")
        raise HTTPException(status_code=500, detail="Failed to get event types")


# Service metrics endpoints
@app.get("/api/v1/analytics/metrics")
async def get_service_metrics(user=Depends(authenticate_user)):
    """Get analytics service metrics"""
    try:
        metrics = await analytics_service.get_metrics()
        return APIResponse(
            success=True,
            message="Service metrics retrieved successfully",
            data=metrics
        )
    except Exception as e:
        logger.error(f"Failed to get service metrics: {e}")
        raise HTTPException(status_code=500, detail="Failed to get service metrics")


@app.get("/api/v1/analytics/windows/{window_name}")
async def get_window_data(
    window_name: str,
    user=Depends(authenticate_user)
):
    """Get data from specific processing window"""
    try:
        data = await analytics_service.get_window_data(window_name)
        return APIResponse(
            success=True,
            message=f"Window data retrieved for {window_name}",
            data=data
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to get window data: {e}")
        raise HTTPException(status_code=500, detail="Failed to get window data")


async def run_analytics_processing():
    """Run analytics processing in background"""
    try:
        await analytics_service.start()
        
        # Keep service running
        while analytics_service.is_running:
            await asyncio.sleep(1)
            
    except KeyboardInterrupt:
        logger.info("Received shutdown signal")
    except Exception as e:
        logger.error(f"Analytics processing error: {e}")
    finally:
        await analytics_service.stop()


if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=settings.services.analytics_port,
        log_level="info",
        reload=settings.debug
    )
