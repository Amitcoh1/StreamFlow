"""
Refactored Event Ingestion Service with Clean Code Principles
StreamFlow - real-time analytics pipeline

This module implements the Event Ingestion Service following clean architecture,
SOLID principles, and design patterns for code.

 
"""
import asyncio
import logging
from abc import ABC, abstractmethod
from contextlib import asynccontextmanager
from datetime import datetime
from typing import Dict, List, Optional, Protocol
from uuid import UUID

from fastapi import FastAPI, HTTPException, Depends, BackgroundTasks, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, Field
import structlog
import uvicorn

from streamflow.shared.config import get_settings
from streamflow.shared.models import Event, EventType, EventSeverity, HealthCheck, HealthStatus, APIResponse
from streamflow.shared.messaging import MessageBroker
from streamflow.shared.database import DatabaseManager

# Configure structured logging
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

logger = structlog.get_logger(__name__)

# Global settings
settings = get_settings()
security = HTTPBearer()


# Domain Models
class EventCreateRequest(BaseModel):
    """Request model for creating events"""
    type: EventType
    source: str = Field(..., min_length=1, max_length=100)
    data: Dict[str, any] = Field(default_factory=dict)
    severity: EventSeverity = Field(default=EventSeverity.MEDIUM)
    correlation_id: Optional[str] = Field(None, max_length=100)
    session_id: Optional[str] = Field(None, max_length=100)
    user_id: Optional[str] = Field(None, max_length=100)
    tags: List[str] = Field(default_factory=list, max_items=10)

    class Config:
        schema_extra = {
            "example": {
                "type": "web.click",
                "source": "web-app",
                "data": {"element": "button", "page": "/home"},
                "severity": "medium",
                "user_id": "user123",
                "tags": ["ui", "interaction"]
            }
        }


class BatchEventRequest(BaseModel):
    """Request model for batch event creation"""
    events: List[EventCreateRequest] = Field(..., min_items=1, max_items=100)


class WebSocketMessage(BaseModel):
    """WebSocket message model"""
    type: str = Field(..., regex="^(event|ping|subscribe|unsubscribe)$")
    data: Dict[str, any] = Field(default_factory=dict)
    correlation_id: Optional[str] = None


# Interfaces (Protocols)
class EventValidator(Protocol):
    """Protocol for event validation"""
    
    def validate(self, event_request: EventCreateRequest) -> bool:
        """Validate event request"""
        ...


class EventPublisher(Protocol):
    """Protocol for event publishing"""
    
    async def publish(self, event: Event) -> bool:
        """Publish event to message broker"""
        ...


class AuthenticationService(Protocol):
    """Protocol for authentication"""
    
    async def authenticate(self, credentials: str) -> Dict[str, any]:
        """Authenticate user credentials"""
        ...


class ConnectionManager(Protocol):
    """Protocol for WebSocket connection management"""
    
    async def connect(self, websocket: WebSocket) -> None:
        """Accept WebSocket connection"""
        ...
    
    def disconnect(self, websocket: WebSocket) -> None:
        """Remove WebSocket connection"""
        ...
    
    async def broadcast(self, message: str) -> None:
        """Broadcast message to all connections"""
        ...


# Implementations
class DefaultEventValidator:
    """Default event validator implementation"""
    
    def validate(self, event_request: EventCreateRequest) -> bool:
        """Validate event request"""
        # Business logic validation
        if not event_request.source:
            return False
        
        if event_request.type == EventType.ERROR and event_request.severity == EventSeverity.LOW:
            return False
        
        # Check for required fields based on event type
        if event_request.type == EventType.USER_LOGIN and not event_request.user_id:
            return False
        
        return True


class RabbitMQEventPublisher:
    """RabbitMQ event publisher implementation"""
    
    def __init__(self, message_broker: MessageBroker):
        self.message_broker = message_broker
    
    async def publish(self, event: Event) -> bool:
        """Publish event to RabbitMQ"""
        try:
            await self.message_broker.publish_event(event)
            logger.info(
                "Event published successfully",
                event_id=str(event.id),
                event_type=event.type,
                source=event.source
            )
            return True
        except Exception as e:
            logger.error(
                "Failed to publish event",
                event_id=str(event.id),
                error=str(e)
            )
            return False


class JWTAuthenticationService:
    """JWT authentication service implementation"""
    
    def __init__(self, secret_key: str):
        self.secret_key = secret_key
    
    async def authenticate(self, credentials: str) -> Dict[str, any]:
        """Authenticate JWT token"""
        # In production, implement proper JWT validation
        # For demo purposes, accept any non-empty token
        if not credentials:
            raise HTTPException(status_code=401, detail="Invalid authentication credentials")
        
        # Mock user data
        return {
            "user_id": "authenticated_user",
            "username": "demo_user",
            "roles": ["user"]
        }


class WebSocketConnectionManager:
    """WebSocket connection manager implementation"""
    
    def __init__(self):
        self.active_connections: List[WebSocket] = []
        self.connection_metadata: Dict[WebSocket, Dict[str, any]] = {}
    
    async def connect(self, websocket: WebSocket) -> None:
        """Accept WebSocket connection"""
        await websocket.accept()
        self.active_connections.append(websocket)
        self.connection_metadata[websocket] = {
            "connected_at": datetime.now(),
            "events_processed": 0
        }
        
        logger.info(
            "WebSocket connection established",
            total_connections=len(self.active_connections),
            client_host=websocket.client.host if websocket.client else None
        )
    
    def disconnect(self, websocket: WebSocket) -> None:
        """Remove WebSocket connection"""
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
            self.connection_metadata.pop(websocket, None)
            
            logger.info(
                "WebSocket connection closed",
                total_connections=len(self.active_connections)
            )
    
    async def send_personal_message(self, message: str, websocket: WebSocket) -> None:
        """Send message to specific WebSocket"""
        try:
            await websocket.send_text(message)
        except Exception as e:
            logger.warning(
                "Failed to send WebSocket message",
                error=str(e)
            )
    
    async def broadcast(self, message: str) -> None:
        """Broadcast message to all connected WebSockets"""
        disconnected_connections = []
        
        for connection in self.active_connections:
            try:
                await connection.send_text(message)
            except Exception as e:
                logger.warning(
                    "Failed to broadcast to WebSocket",
                    error=str(e)
                )
                disconnected_connections.append(connection)
        
        # Clean up disconnected connections
        for connection in disconnected_connections:
            self.disconnect(connection)


# Service Layer
class EventIngestionService:
    """Main event ingestion service"""
    
    def __init__(
        self,
        validator: EventValidator,
        publisher: EventPublisher,
        auth_service: AuthenticationService,
        connection_manager: ConnectionManager
    ):
        self.validator = validator
        self.publisher = publisher
        self.auth_service = auth_service
        self.connection_manager = connection_manager
        self.metrics = {
            "events_processed": 0,
            "events_failed": 0,
            "websocket_connections": 0
        }
    
    async def create_event(
        self,
        event_request: EventCreateRequest,
        user_context: Dict[str, any]
    ) -> Event:
        """Create and validate event"""
        # Validate event
        if not self.validator.validate(event_request):
            self.metrics["events_failed"] += 1
            raise HTTPException(status_code=400, detail="Event validation failed")
        
        # Create event
        event = Event(
            type=event_request.type,
            source=event_request.source,
            data=event_request.data,
            severity=event_request.severity,
            correlation_id=event_request.correlation_id,
            session_id=event_request.session_id,
            user_id=event_request.user_id or user_context.get("user_id"),
            tags=event_request.tags
        )
        
        logger.info(
            "Event created",
            event_id=str(event.id),
            event_type=event.type,
            source=event.source,
            user_id=event.user_id
        )
        
        return event
    
    async def publish_event(self, event: Event) -> bool:
        """Publish event to message broker"""
        success = await self.publisher.publish(event)
        
        if success:
            self.metrics["events_processed"] += 1
        else:
            self.metrics["events_failed"] += 1
        
        return success
    
    async def create_events_batch(
        self,
        batch_request: BatchEventRequest,
        user_context: Dict[str, any]
    ) -> List[Event]:
        """Create multiple events in batch"""
        events = []
        
        for event_request in batch_request.events:
            try:
                event = await self.create_event(event_request, user_context)
                events.append(event)
            except HTTPException as e:
                logger.warning(
                    "Failed to create event in batch",
                    error=str(e),
                    event_data=event_request.dict()
                )
                # Continue processing other events
                continue
        
        return events
    
    async def publish_events_batch(self, events: List[Event]) -> Dict[str, int]:
        """Publish multiple events concurrently"""
        tasks = [self.publish_event(event) for event in events]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        successful = sum(1 for result in results if result is True)
        failed = len(results) - successful
        
        logger.info(
            "Batch processing completed",
            total_events=len(events),
            successful=successful,
            failed=failed
        )
        
        return {"successful": successful, "failed": failed}
    
    def get_metrics(self) -> Dict[str, any]:
        """Get service metrics"""
        return {
            **self.metrics,
            "websocket_connections": len(self.connection_manager.active_connections),
            "timestamp": datetime.now().isoformat()
        }


# Global instances
event_validator = DefaultEventValidator()
message_broker = None
event_publisher = None
auth_service = JWTAuthenticationService(settings.jwt_secret_key)
connection_manager = WebSocketConnectionManager()
ingestion_service = None


async def get_ingestion_service() -> EventIngestionService:
    """Get event ingestion service instance"""
    global ingestion_service
    if ingestion_service is None:
        ingestion_service = EventIngestionService(
            validator=event_validator,
            publisher=event_publisher,
            auth_service=auth_service,
            connection_manager=connection_manager
        )
    return ingestion_service


async def authenticate_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Authenticate user"""
    return await auth_service.authenticate(credentials.credentials)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    global message_broker, event_publisher
    
    # Startup
    logger.info("Starting Event Ingestion Service...")
    
    # Initialize dependencies
    message_broker = MessageBroker(settings)
    await message_broker.initialize()
    
    event_publisher = RabbitMQEventPublisher(message_broker)
    
    logger.info("Event Ingestion Service started successfully!")
    
    yield
    
    # Shutdown
    logger.info("Shutting down Event Ingestion Service...")
    
    if message_broker:
        await message_broker.close()
    
    logger.info("Event Ingestion Service stopped")


# Create FastAPI app
app = FastAPI(
    title="StreamFlow Event Ingestion Service",
    description="event ingestion service with clean architecture",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# API Endpoints
@app.get("/health", response_model=HealthCheck)
async def health_check(service: EventIngestionService = Depends(get_ingestion_service)):
    """Health check endpoint"""
    try:
        # Check dependencies
        broker_healthy = message_broker and message_broker.is_connected
        
        overall_status = HealthStatus.HEALTHY if broker_healthy else HealthStatus.UNHEALTHY
        
        return HealthCheck(
            status=overall_status,
            service="ingestion",
            version="1.0.0",
            checks={
                "message_broker": {"status": "healthy" if broker_healthy else "unhealthy"},
                "websocket_connections": len(connection_manager.active_connections),
                "metrics": service.get_metrics()
            }
        )
    except Exception as e:
        logger.error("Health check failed", error=str(e))
        return HealthCheck(
            status=HealthStatus.UNHEALTHY,
            service="ingestion",
            version="1.0.0",
            checks={"error": str(e)}
        )


@app.get("/ready")
async def readiness_check():
    """Readiness check endpoint"""
    return {"status": "ready", "service": "ingestion"}


@app.post("/events", response_model=APIResponse)
async def create_event(
    event_request: EventCreateRequest,
    background_tasks: BackgroundTasks,
    user=Depends(authenticate_user),
    service: EventIngestionService = Depends(get_ingestion_service)
):
    """Create a single event"""
    try:
        event = await service.create_event(event_request, user)
        
        # Publish event asynchronously
        background_tasks.add_task(service.publish_event, event)
        
        return APIResponse(
            success=True,
            message="Event created successfully",
            data={"event_id": str(event.id)},
            correlation_id=event.correlation_id
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to create event", error=str(e))
        raise HTTPException(status_code=500, detail="Internal server error")


@app.post("/events/batch", response_model=APIResponse)
async def create_events_batch(
    batch_request: BatchEventRequest,
    background_tasks: BackgroundTasks,
    user=Depends(authenticate_user),
    service: EventIngestionService = Depends(get_ingestion_service)
):
    """Create multiple events in batch"""
    try:
        events = await service.create_events_batch(batch_request, user)
        
        if not events:
            raise HTTPException(status_code=400, detail="No valid events in batch")
        
        # Publish events asynchronously
        background_tasks.add_task(service.publish_events_batch, events)
        
        return APIResponse(
            success=True,
            message=f"Batch of {len(events)} events created successfully",
            data={"event_ids": [str(event.id) for event in events]}
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to create event batch", error=str(e))
        raise HTTPException(status_code=500, detail="Internal server error")


@app.get("/events/{event_id}")
async def get_event(
    event_id: UUID,
    user=Depends(authenticate_user)
):
    """Get event by ID (placeholder implementation)"""
    return APIResponse(
        success=True,
        message="Event retrieved successfully",
        data={"event_id": str(event_id), "status": "placeholder"}
    )


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time event streaming"""
    await connection_manager.connect(websocket)
    
    try:
        while True:
            data = await websocket.receive_text()
            
            try:
                message = WebSocketMessage.parse_raw(data)
                
                if message.type == "event":
                    # Process event from WebSocket
                    event_request = EventCreateRequest(
                        type=EventType.CUSTOM,
                        source="websocket",
                        data=message.data,
                        correlation_id=message.correlation_id
                    )
                    
                    # Create dummy user context for WebSocket
                    user_context = {"user_id": "websocket_user"}
                    service = await get_ingestion_service()
                    
                    event = await service.create_event(event_request, user_context)
                    await service.publish_event(event)
                    
                    await connection_manager.send_personal_message(
                        f"Event {event.id} processed successfully",
                        websocket
                    )
                
                elif message.type == "ping":
                    await connection_manager.send_personal_message("pong", websocket)
                
            except Exception as e:
                logger.error(
                    "WebSocket message processing error",
                    error=str(e),
                    message_data=data
                )
                await connection_manager.send_personal_message(
                    f"Error processing message: {str(e)}",
                    websocket
                )
                
    except WebSocketDisconnect:
        connection_manager.disconnect(websocket)
    except Exception as e:
        logger.error("WebSocket error", error=str(e))
        connection_manager.disconnect(websocket)


@app.get("/metrics")
async def get_metrics(service: EventIngestionService = Depends(get_ingestion_service)):
    """Get service metrics"""
    return service.get_metrics()


if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=settings.services.ingestion_port,
        log_level="info",
        reload=settings.debug,
        access_log=True
    )
