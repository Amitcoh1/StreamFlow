"""
Dashboard API Service - Real-time metrics and dashboard endpoints
StreamFlow - real-time analytics pipeline

 
"""
import asyncio
import logging
from contextlib import asynccontextmanager
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Union
from uuid import UUID

from fastapi import FastAPI, HTTPException, Depends, WebSocket, WebSocketDisconnect, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.responses import JSONResponse, Response
from pydantic import BaseModel, Field
import uvicorn
import json
import httpx
from prometheus_client import Counter, Histogram, generate_latest
from prometheus_client.openmetrics.exposition import CONTENT_TYPE_LATEST

from streamflow.shared.config import get_settings
from streamflow.shared.models import (
    HealthCheck, HealthStatus, APIResponse, PaginatedResponse, 
    PaginationParams, MetricData, Event, Alert
)
from streamflow.shared.messaging import get_message_broker, get_event_publisher
from streamflow.shared.database import get_database_manager

logger = logging.getLogger(__name__)

# Global state
settings = get_settings()
security = HTTPBearer()


class MetricRequest(BaseModel):
    """Request model for metrics"""
    name: str
    start_time: datetime
    end_time: datetime
    interval: str = Field(default="1m", description="Aggregation interval")
    filters: Dict[str, Any] = Field(default_factory=dict)


class DashboardWidget(BaseModel):
    """Dashboard widget configuration"""
    id: str
    type: str  # chart, table, metric, alert
    title: str
    config: Dict[str, Any]
    position: Dict[str, int]  # x, y, width, height
    refresh_interval: int = Field(default=30, description="Refresh interval in seconds")


class Dashboard(BaseModel):
    """Dashboard configuration"""
    id: str
    name: str
    description: Optional[str] = None
    widgets: List[DashboardWidget]
    layout: Dict[str, Any] = Field(default_factory=dict)
    is_public: bool = Field(default=False)
    created_by: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class RealtimeMetricsManager:
    """Manages real-time metrics collection and distribution"""
    
    def __init__(self):
        self.metrics_cache: Dict[str, Any] = {}
        self.websocket_connections: List[WebSocket] = []
        self.metric_history: Dict[str, List[Dict[str, Any]]] = {}
        self.max_history_size = 1000
    
    async def add_connection(self, websocket: WebSocket):
        """Add WebSocket connection"""
        await websocket.accept()
        self.websocket_connections.append(websocket)
        logger.info(f"WebSocket connected. Total connections: {len(self.websocket_connections)}")
    
    def remove_connection(self, websocket: WebSocket):
        """Remove WebSocket connection"""
        if websocket in self.websocket_connections:
            self.websocket_connections.remove(websocket)
            logger.info(f"WebSocket disconnected. Total connections: {len(self.websocket_connections)}")
    
    async def broadcast_metric(self, metric: Dict[str, Any]):
        """Broadcast metric to all connected clients"""
        if not self.websocket_connections:
            return
        
        message = json.dumps({
            "type": "metric",
            "data": metric,
            "timestamp": datetime.utcnow().isoformat()
        })
        
        # Send to all connections
        disconnected = []
        for connection in self.websocket_connections:
            try:
                await connection.send_text(message)
            except Exception as e:
                logger.warning(f"Failed to send to WebSocket: {e}")
                disconnected.append(connection)
        
        # Remove disconnected connections
        for connection in disconnected:
            self.remove_connection(connection)
    
    async def update_metric(self, metric_name: str, value: Any, tags: Optional[Dict[str, str]] = None):
        """Update metric value"""
        metric_data = {
            "name": metric_name,
            "value": value,
            "tags": tags or {},
            "timestamp": datetime.utcnow().isoformat()
        }
        
        # Update cache
        self.metrics_cache[metric_name] = metric_data
        
        # Add to history
        if metric_name not in self.metric_history:
            self.metric_history[metric_name] = []
        
        self.metric_history[metric_name].append(metric_data)
        
        # Limit history size
        if len(self.metric_history[metric_name]) > self.max_history_size:
            self.metric_history[metric_name] = self.metric_history[metric_name][-self.max_history_size:]
        
        # Broadcast to WebSocket clients
        await self.broadcast_metric(metric_data)
    
    def get_current_metrics(self) -> Dict[str, Any]:
        """Get current metric values"""
        return self.metrics_cache.copy()
    
    def get_metric_history(self, metric_name: str, limit: int = 100) -> List[Dict[str, Any]]:
        """Get metric history"""
        history = self.metric_history.get(metric_name, [])
        return history[-limit:] if history else []


class DashboardManager:
    """Manages dashboard configurations"""
    
    def __init__(self):
        self.dashboards: Dict[str, Dashboard] = {}
        self._create_default_dashboards()
    
    def _create_default_dashboards(self):
        """Create default dashboards"""
        # System Overview Dashboard
        system_dashboard = Dashboard(
            id="system-overview",
            name="System Overview",
            description="Overall system health and performance",
            widgets=[
                DashboardWidget(
                    id="events-per-second",
                    type="metric",
                    title="Events per Second",
                    config={"metric": "events_per_second", "format": "number"},
                    position={"x": 0, "y": 0, "width": 3, "height": 2}
                ),
                DashboardWidget(
                    id="active-alerts",
                    type="metric",
                    title="Active Alerts",
                    config={"metric": "active_alerts", "format": "number"},
                    position={"x": 3, "y": 0, "width": 3, "height": 2}
                ),
                DashboardWidget(
                    id="error-rate",
                    type="chart",
                    title="Error Rate",
                    config={"metric": "error_rate", "chart_type": "line", "time_range": "1h"},
                    position={"x": 0, "y": 2, "width": 6, "height": 4}
                ),
                DashboardWidget(
                    id="recent-events",
                    type="table",
                    title="Recent Events",
                    config={"source": "events", "limit": 10},
                    position={"x": 6, "y": 0, "width": 6, "height": 6}
                )
            ],
            created_by="system",
            is_public=True
        )
        
        self.dashboards[system_dashboard.id] = system_dashboard
        
        # Analytics Dashboard
        analytics_dashboard = Dashboard(
            id="analytics-overview",
            name="Analytics Overview",
            description="Real-time analytics and insights",
            widgets=[
                DashboardWidget(
                    id="user-activity",
                    type="chart",
                    title="User Activity",
                    config={"metric": "user_activity", "chart_type": "area", "time_range": "24h"},
                    position={"x": 0, "y": 0, "width": 6, "height": 4}
                ),
                DashboardWidget(
                    id="top-events",
                    type="chart",
                    title="Top Event Types",
                    config={"metric": "event_types", "chart_type": "pie"},
                    position={"x": 6, "y": 0, "width": 6, "height": 4}
                )
            ],
            created_by="system",
            is_public=True
        )
        
        self.dashboards[analytics_dashboard.id] = analytics_dashboard
    
    async def get_dashboard(self, dashboard_id: str) -> Optional[Dashboard]:
        """Get dashboard by ID"""
        return self.dashboards.get(dashboard_id)
    
    async def list_dashboards(self) -> List[Dashboard]:
        """List all dashboards"""
        return list(self.dashboards.values())
    
    async def create_dashboard(self, dashboard: Dashboard) -> Dashboard:
        """Create new dashboard"""
        self.dashboards[dashboard.id] = dashboard
        return dashboard
    
    async def update_dashboard(self, dashboard_id: str, dashboard: Dashboard) -> Optional[Dashboard]:
        """Update dashboard"""
        if dashboard_id in self.dashboards:
            dashboard.updated_at = datetime.utcnow()
            self.dashboards[dashboard_id] = dashboard
            return dashboard
        return None
    
    async def delete_dashboard(self, dashboard_id: str) -> bool:
        """Delete dashboard"""
        if dashboard_id in self.dashboards:
            del self.dashboards[dashboard_id]
            return True
        return False


# Global managers
metrics_manager = RealtimeMetricsManager()
dashboard_manager = DashboardManager()


async def authenticate_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Authenticate user"""
    if not credentials.credentials:
        raise HTTPException(status_code=401, detail="Invalid authentication credentials")
    return {"user_id": "authenticated_user"}


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events"""
    # Startup
    logger.info("Starting Dashboard API Service...")
    
    # Initialize message broker
    broker = await get_message_broker()
    
    # Initialize database
    db_manager = await get_database_manager()
    await db_manager.create_tables()
    
    # Start metrics collection
    asyncio.create_task(collect_metrics())
    
    logger.info("Dashboard API Service started successfully")
    
    yield
    
    # Shutdown
    logger.info("Shutting down Dashboard API Service...")
    
    # Cleanup resources
    await broker.disconnect()
    await db_manager.close()
    
    logger.info("Dashboard API Service stopped")


# Create FastAPI app
app = FastAPI(
    title="StreamFlow Dashboard API",
    description="Real-time dashboard and metrics API",
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
            service="dashboard",
            version="0.1.0",
            checks={
                "database": db_health,
                "message_broker": broker_health,
                "websocket_connections": len(metrics_manager.websocket_connections),
                "dashboards_count": len(dashboard_manager.dashboards)
            }
        )
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return HealthCheck(
            status=HealthStatus.UNHEALTHY,
            service="dashboard",
            version="0.1.0",
            checks={"error": str(e)}
        )


@app.get("/ready")
async def readiness_check():
    """Readiness check endpoint"""
    return {"status": "ready", "service": "dashboard"}


@app.get("/metrics")
async def get_prometheus_metrics():
    """Prometheus metrics endpoint"""
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)


# Metrics endpoints
@app.get("/metrics/realtime")
async def get_realtime_metrics(user=Depends(authenticate_user)):
    """Get real-time metrics"""
    try:
        metrics = metrics_manager.get_current_metrics()
        return APIResponse(
            success=True,
            message="Real-time metrics retrieved successfully",
            data=metrics
        )
    except Exception as e:
        logger.error(f"Failed to get real-time metrics: {e}")
        raise HTTPException(status_code=500, detail="Failed to get real-time metrics")


@app.get("/metrics/history/{metric_name}")
async def get_metric_history(
    metric_name: str,
    limit: int = Query(default=100, ge=1, le=1000),
    user=Depends(authenticate_user)
):
    """Get metric history"""
    try:
        history = metrics_manager.get_metric_history(metric_name, limit)
        return APIResponse(
            success=True,
            message=f"Metric history retrieved for {metric_name}",
            data=history
        )
    except Exception as e:
        logger.error(f"Failed to get metric history: {e}")
        raise HTTPException(status_code=500, detail="Failed to get metric history")


@app.post("/metrics/query")
async def query_metrics(
    request: MetricRequest,
    user=Depends(authenticate_user)
):
    """Query metrics with filters"""
    try:
        # This would integrate with actual time-series database
        # For now, return mock data
        mock_data = [
            {
                "timestamp": request.start_time.isoformat(),
                "value": 100.0,
                "tags": {"service": "ingestion"}
            },
            {
                "timestamp": request.end_time.isoformat(),
                "value": 150.0,
                "tags": {"service": "ingestion"}
            }
        ]
        
        return APIResponse(
            success=True,
            message="Metrics queried successfully",
            data=mock_data
        )
    except Exception as e:
        logger.error(f"Failed to query metrics: {e}")
        raise HTTPException(status_code=500, detail="Failed to query metrics")


# Dashboard endpoints
@app.get("/dashboards")
async def list_dashboards(user=Depends(authenticate_user)):
    """List all dashboards"""
    try:
        dashboards = await dashboard_manager.list_dashboards()
        return APIResponse(
            success=True,
            message="Dashboards retrieved successfully",
            data=[dashboard.dict() for dashboard in dashboards]
        )
    except Exception as e:
        logger.error(f"Failed to list dashboards: {e}")
        raise HTTPException(status_code=500, detail="Failed to list dashboards")


@app.get("/dashboards/{dashboard_id}")
async def get_dashboard(dashboard_id: str, user=Depends(authenticate_user)):
    """Get dashboard by ID"""
    try:
        dashboard = await dashboard_manager.get_dashboard(dashboard_id)
        if not dashboard:
            raise HTTPException(status_code=404, detail="Dashboard not found")
        
        return APIResponse(
            success=True,
            message="Dashboard retrieved successfully",
            data=dashboard.dict()
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get dashboard: {e}")
        raise HTTPException(status_code=500, detail="Failed to get dashboard")


@app.post("/dashboards")
async def create_dashboard(
    dashboard: Dashboard,
    user=Depends(authenticate_user)
):
    """Create new dashboard"""
    try:
        dashboard.created_by = user["user_id"]
        created_dashboard = await dashboard_manager.create_dashboard(dashboard)
        
        return APIResponse(
            success=True,
            message="Dashboard created successfully",
            data=created_dashboard.dict()
        )
    except Exception as e:
        logger.error(f"Failed to create dashboard: {e}")
        raise HTTPException(status_code=500, detail="Failed to create dashboard")


@app.put("/dashboards/{dashboard_id}")
async def update_dashboard(
    dashboard_id: str,
    dashboard: Dashboard,
    user=Depends(authenticate_user)
):
    """Update dashboard"""
    try:
        updated_dashboard = await dashboard_manager.update_dashboard(dashboard_id, dashboard)
        if not updated_dashboard:
            raise HTTPException(status_code=404, detail="Dashboard not found")
        
        return APIResponse(
            success=True,
            message="Dashboard updated successfully",
            data=updated_dashboard.dict()
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update dashboard: {e}")
        raise HTTPException(status_code=500, detail="Failed to update dashboard")


@app.delete("/dashboards/{dashboard_id}")
async def delete_dashboard(
    dashboard_id: str,
    user=Depends(authenticate_user)
):
    """Delete dashboard"""
    try:
        deleted = await dashboard_manager.delete_dashboard(dashboard_id)
        if not deleted:
            raise HTTPException(status_code=404, detail="Dashboard not found")
        
        return APIResponse(
            success=True,
            message="Dashboard deleted successfully"
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete dashboard: {e}")
        raise HTTPException(status_code=500, detail="Failed to delete dashboard")


# Events endpoints
@app.get("/api/v1/events")
async def get_events(
    limit: int = Query(default=50, ge=1, le=1000),
    offset: int = Query(default=0, ge=0),
    event_type: Optional[str] = Query(default=None),
    user=Depends(authenticate_user)
):
    """Get recent events from storage service"""
    
    try:
        # Query storage service for events
        storage_url = f"http://storage:8005/api/v1/events/query"
        query_data = {
            "limit": limit,
            "offset": offset
        }
        
        if event_type:
            # Convert string to EventType enum format
            query_data["event_types"] = [event_type]
        
        async with httpx.AsyncClient() as client:
            response = await client.post(storage_url, json=query_data, timeout=10)
            response.raise_for_status()
            events = response.json()
        
        return APIResponse(
            success=True,
            message="Events retrieved successfully",
            data=events
        )
    except httpx.RequestError as e:
        logger.error(f"Failed to connect to storage service: {e}")
        # Return empty list if storage service is unavailable
        return APIResponse(
            success=True,
            message="Storage service unavailable, returning empty list",
            data=[]
        )
    except Exception as e:
        logger.error(f"Failed to get events: {e}")
        raise HTTPException(status_code=500, detail="Failed to get events")


@app.get("/api/v1/stats")
async def get_dashboard_stats(user=Depends(authenticate_user)):
    """Get dashboard statistics including real events count"""
    
    try:
        # Get storage stats from storage service
        storage_stats = {}
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get("http://storage:8005/api/v1/stats", timeout=10)
                response.raise_for_status()
                storage_stats = response.json()
        except Exception as e:
            logger.warning(f"Could not get storage stats: {e}")
            storage_stats = {
                "total_events": 0,
                "events_by_type": {},
                "events_by_source": {}
            }
        
        # Get current metrics
        current_metrics = metrics_manager.get_current_metrics()
        
        # Combine stats
        dashboard_stats = {
            "total_events": storage_stats.get("total_events", 0),
            "events_by_type": storage_stats.get("events_by_type", {}),
            "events_by_source": storage_stats.get("events_by_source", {}),
            "real_time_metrics": current_metrics,
            "active_connections": len(metrics_manager.websocket_connections),
            "storage_health": "connected" if storage_stats else "disconnected"
        }
        
        return APIResponse(
            success=True,
            message="Dashboard stats retrieved successfully",
            data=dashboard_stats
        )
    except Exception as e:
        logger.error(f"Failed to get dashboard stats: {e}")
        raise HTTPException(status_code=500, detail="Failed to get dashboard stats")


# WebSocket endpoints
@app.websocket("/ws/metrics")
async def websocket_metrics(websocket: WebSocket):
    """WebSocket endpoint for real-time metrics"""
    await metrics_manager.add_connection(websocket)
    
    try:
        while True:
            # Keep connection alive and handle incoming messages
            data = await websocket.receive_text()
            
            # Handle ping/pong
            if data == "ping":
                await websocket.send_text("pong")
                
    except WebSocketDisconnect:
        metrics_manager.remove_connection(websocket)
        logger.info("WebSocket client disconnected")
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        metrics_manager.remove_connection(websocket)


@app.websocket("/ws/alerts")
async def websocket_alerts(websocket: WebSocket):
    """WebSocket endpoint for real-time alerts"""
    await websocket.accept()
    
    try:
        while True:
            # This would integrate with alert service
            # For now, just keep connection alive
            await asyncio.sleep(1)
                
    except WebSocketDisconnect:
        logger.info("Alert WebSocket client disconnected")
    except Exception as e:
        logger.error(f"Alert WebSocket error: {e}")


# Background task for metrics collection
async def collect_metrics():
    """Collect metrics from various sources"""
    while True:
        try:
            # Collect system metrics
            await metrics_manager.update_metric("events_per_second", 125.5)
            await metrics_manager.update_metric("active_alerts", 3)
            await metrics_manager.update_metric("error_rate", 0.02)
            await metrics_manager.update_metric("response_time_avg", 0.234)
            await metrics_manager.update_metric("active_connections", len(metrics_manager.websocket_connections))
            
            # Sleep before next collection
            await asyncio.sleep(5)  # Collect every 5 seconds
            
        except Exception as e:
            logger.error(f"Metrics collection error: {e}")
            await asyncio.sleep(5)


if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=settings.services.dashboard_port,
        log_level="info",
        reload=settings.debug
    )
