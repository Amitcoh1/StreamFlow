"""
Event Ingestion Service - FastAPI application for collecting events
StreamFlow - real-time analytics pipeline

 
"""
import asyncio
import logging
from contextlib import asynccontextmanager
from datetime import datetime
from typing import Dict, List, Optional, Any
from uuid import UUID

from fastapi import FastAPI, HTTPException, Depends, BackgroundTasks, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, Field
import uvicorn

from streamflow.shared.config import get_settings
from streamflow.shared.models import Event, EventType, EventSeverity, HealthCheck, HealthStatus, APIResponse
from streamflow.shared.messaging import get_message_broker, get_event_publisher
from streamflow.shared.database import get_database_manager

logger = logging.getLogger(__name__)

# Global state
settings = get_settings()
security = HTTPBearer()


class EventCreateRequest(BaseModel):
    """Request model for creating events"""
    type: EventType
    source: str
    data: Dict[str, Any] = Field(default_factory=dict)
    severity: EventSeverity = Field(default=EventSeverity.MEDIUM)
    correlation_id: Optional[str] = None
    session_id: Optional[str] = None
    user_id: Optional[str] = None
    tags: List[str] = Field(default_factory=list)


class BatchEventRequest(BaseModel):
    """Request model for batch event creation"""
    events: List[EventCreateRequest]


class WebSocketMessage(BaseModel):
    """WebSocket message model"""
    type: str
    data: Dict[str, Any]


class ConnectionManager:
    """WebSocket connection manager"""
    
    def __init__(self):
        self.active_connections: List[WebSocket] = []
    
    async def connect(self, websocket: WebSocket):
        """Accept WebSocket connection"""
        await websocket.accept()
        self.active_connections.append(websocket)
        logger.info(f"WebSocket connection established. Total connections: {len(self.active_connections)}")
    
    def disconnect(self, websocket: WebSocket):
        """Remove WebSocket connection"""
        self.active_connections.remove(websocket)
        logger.info(f"WebSocket connection closed. Total connections: {len(self.active_connections)}")
    
    async def send_personal_message(self, message: str, websocket: WebSocket):
        """Send message to specific WebSocket"""
        await websocket.send_text(message)
    
    async def broadcast(self, message: str):
        """Broadcast message to all connected WebSockets"""
        for connection in self.active_connections:
            try:
                await connection.send_text(message)
            except Exception as e:
                logger.warning(f"Failed to send message to WebSocket: {e}")


# Global connection manager
manager = ConnectionManager()


async def authenticate_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Authenticate user (placeholder implementation)"""
    # In production, implement proper JWT validation
    if not credentials.credentials:
        raise HTTPException(status_code=401, detail="Invalid authentication credentials")
    return {"user_id": "authenticated_user"}


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events"""
    # Startup
    logger.info("Starting Event Ingestion Service...")
    
    # Initialize message broker
    broker = await get_message_broker()
    
    # Initialize database
    db_manager = await get_database_manager()
    await db_manager.create_tables()
    
    logger.info("Event Ingestion Service started successfully")
    
    yield
    
    # Shutdown
    logger.info("Shutting down Event Ingestion Service...")
    
    # Cleanup resources
    await broker.disconnect()
    await db_manager.close()
    
    logger.info("Event Ingestion Service stopped")


# Create FastAPI app
app = FastAPI(
    title="StreamFlow Event Ingestion Service",
    description="event ingestion service with REST and WebSocket support",
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

# Rate limiting middleware (simplified)
@app.middleware("http")
async def rate_limit_middleware(request, call_next):
    """Basic rate limiting middleware"""
    # In production, implement proper rate limiting with Redis
    response = await call_next(request)
    return response


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
            service="ingestion",
            version="0.1.0",
            checks={
                "database": db_health,
                "message_broker": broker_health,
                "websocket_connections": len(manager.active_connections)
            }
        )
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return HealthCheck(
            status=HealthStatus.UNHEALTHY,
            service="ingestion",
            version="0.1.0",
            checks={"error": str(e)}
        )


@app.get("/ready")
async def readiness_check():
    """Readiness check endpoint"""
    return {"status": "ready", "service": "ingestion"}


# Event ingestion endpoints
@app.post("/events", response_model=APIResponse)
async def create_event(
    event_request: EventCreateRequest,
    background_tasks: BackgroundTasks,
    user=Depends(authenticate_user)
):
    """Create a single event"""
    try:
        # Create event
        event = Event(
            type=event_request.type,
            source=event_request.source,
            data=event_request.data,
            severity=event_request.severity,
            correlation_id=event_request.correlation_id,
            session_id=event_request.session_id,
            user_id=event_request.user_id or user.get("user_id"),
            tags=event_request.tags
        )
        
        # Publish event asynchronously
        background_tasks.add_task(publish_event, event)
        
        return APIResponse(
            success=True,
            message="Event created successfully",
            data={"event_id": str(event.id)}
        )
        
    except Exception as e:
        logger.error(f"Failed to create event: {e}")
        raise HTTPException(status_code=500, detail="Failed to create event")


@app.post("/events/batch", response_model=APIResponse)
async def create_events_batch(
    batch_request: BatchEventRequest,
    background_tasks: BackgroundTasks,
    user=Depends(authenticate_user)
):
    """Create multiple events in batch"""
    try:
        events = []
        for event_request in batch_request.events:
            event = Event(
                type=event_request.type,
                source=event_request.source,
                data=event_request.data,
                severity=event_request.severity,
                correlation_id=event_request.correlation_id,
                session_id=event_request.session_id,
                user_id=event_request.user_id or user.get("user_id"),
                tags=event_request.tags
            )
            events.append(event)
        
        # Publish events asynchronously
        background_tasks.add_task(publish_events_batch, events)
        
        return APIResponse(
            success=True,
            message=f"Batch of {len(events)} events created successfully",
            data={"event_ids": [str(event.id) for event in events]}
        )
        
    except Exception as e:
        logger.error(f"Failed to create event batch: {e}")
        raise HTTPException(status_code=500, detail="Failed to create event batch")


@app.get("/events/{event_id}")
async def get_event(
    event_id: UUID,
    user=Depends(authenticate_user)
):
    """Get event by ID"""
    try:
        # This would typically query the database
        # For now, return a placeholder response
        return APIResponse(
            success=True,
            message="Event retrieved successfully",
            data={"event_id": str(event_id), "status": "placeholder"}
        )
        
    except Exception as e:
        logger.error(f"Failed to get event: {e}")
        raise HTTPException(status_code=404, detail="Event not found")


# WebSocket endpoint
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time event streaming"""
    await manager.connect(websocket)
    
    try:
        while True:
            # Receive message from client
            data = await websocket.receive_text()
            
            try:
                # Parse message
                message = WebSocketMessage.parse_raw(data)
                
                if message.type == "event":
                    # Create event from WebSocket message
                    event = Event(
                        type=EventType.CUSTOM,
                        source="websocket",
                        data=message.data,
                        correlation_id=message.data.get("correlation_id")
                    )
                    
                    # Publish event
                    await publish_event(event)
                    
                    # Send acknowledgment
                    await manager.send_personal_message(
                        f"Event {event.id} processed successfully",
                        websocket
                    )
                
                elif message.type == "ping":
                    await manager.send_personal_message("pong", websocket)
                
            except Exception as e:
                logger.error(f"WebSocket message processing error: {e}")
                await manager.send_personal_message(
                    f"Error processing message: {str(e)}",
                    websocket
                )
                
    except WebSocketDisconnect:
        manager.disconnect(websocket)
        logger.info("WebSocket client disconnected")
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        manager.disconnect(websocket)


# Background tasks
async def publish_event(event: Event):
    """Publish single event to message broker"""
    try:
        publisher = await get_event_publisher()
        await publisher.publish_event(event)
        logger.info(f"Event {event.id} published successfully")
    except Exception as e:
        logger.error(f"Failed to publish event {event.id}: {e}")


async def publish_events_batch(events: List[Event]):
    """Publish multiple events to message broker"""
    try:
        publisher = await get_event_publisher()
        
        # Publish events concurrently
        tasks = [publisher.publish_event(event) for event in events]
        await asyncio.gather(*tasks)
        
        logger.info(f"Batch of {len(events)} events published successfully")
    except Exception as e:
        logger.error(f"Failed to publish event batch: {e}")


# Metrics endpoint
@app.get("/metrics")
async def get_metrics():
    """Get service metrics"""
    return {
        "service": "ingestion",
        "websocket_connections": len(manager.active_connections),
        "timestamp": datetime.utcnow().isoformat()
    }


if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=settings.services.ingestion_port,
        log_level="info",
        reload=settings.debug
    )
