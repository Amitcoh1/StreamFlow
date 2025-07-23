"""
Data Storage Service for StreamFlow
StreamFlow - real-time analytics pipeline

 

This service handles:
- Event data archival and retrieval
- Time-series data storage
- Data lifecycle management
- Data compression and optimization
- Backup and recovery operations
- Data retention policies
"""
import asyncio
import logging
from contextlib import asynccontextmanager
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from uuid import UUID

from fastapi import FastAPI, HTTPException, Depends, BackgroundTasks, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, Response
from pydantic import BaseModel, Field
from prometheus_client import Counter, Histogram, Gauge, generate_latest
from prometheus_client.openmetrics.exposition import CONTENT_TYPE_LATEST

from streamflow.shared.models import Event, EventType, EventSeverity
from streamflow.shared.database import DatabaseManager
from streamflow.shared.messaging import MessageBroker
from streamflow.shared.config import get_settings
from sqlalchemy import text

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Metrics
storage_requests_total = Counter('storage_requests_total', 'Total storage requests', ['operation', 'status'])
storage_request_duration = Histogram('storage_request_duration_seconds', 'Storage request duration', ['operation'])
storage_data_size = Histogram('storage_data_size_bytes', 'Size of stored data', ['operation'])
stored_events_total = Counter('stored_events_total', 'Total events stored', ['event_type'])
data_retention_operations = Counter('data_retention_operations_total', 'Data retention operations', ['operation'])

# Global instances
db_manager = None
message_broker = None
settings = get_settings()


class StorageQuery(BaseModel):
    """Storage query parameters"""
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    event_types: Optional[List[EventType]] = None
    sources: Optional[List[str]] = None
    user_ids: Optional[List[str]] = None
    tags: Optional[List[str]] = None
    limit: int = Field(default=100, le=10000)
    offset: int = Field(default=0, ge=0)


class StorageStats(BaseModel):
    """Storage statistics"""
    total_events: int
    events_by_type: Dict[str, int]
    events_by_source: Dict[str, int]
    storage_size_bytes: int
    oldest_event: Optional[datetime]
    newest_event: Optional[datetime]


class DataRetentionPolicy(BaseModel):
    """Data retention policy"""
    event_type: Optional[EventType] = None
    retention_days: int
    compression_enabled: bool = True
    archive_enabled: bool = True


class StorageService:
    """Main storage service class"""
    
    def __init__(self, db_manager: DatabaseManager, message_broker: MessageBroker):
        self.db_manager = db_manager
        self.message_broker = message_broker
        self.retention_policies: Dict[str, DataRetentionPolicy] = {}
        self._setup_default_policies()
        
    def _setup_default_policies(self):
        """Setup default retention policies"""
        self.retention_policies.update({
            EventType.WEB_CLICK: DataRetentionPolicy(
                event_type=EventType.WEB_CLICK,
                retention_days=30,
                compression_enabled=True,
                archive_enabled=True
            ),
            EventType.WEB_PAGEVIEW: DataRetentionPolicy(
                event_type=EventType.WEB_PAGEVIEW,
                retention_days=90,
                compression_enabled=True,
                archive_enabled=True
            ),
            EventType.API_REQUEST: DataRetentionPolicy(
                event_type=EventType.API_REQUEST,
                retention_days=180,
                compression_enabled=True,
                archive_enabled=True
            ),
            EventType.ERROR: DataRetentionPolicy(
                event_type=EventType.ERROR,
                retention_days=365,
                compression_enabled=False,
                archive_enabled=True
            ),
            EventType.METRIC: DataRetentionPolicy(
                event_type=EventType.METRIC,
                retention_days=365,
                compression_enabled=True,
                archive_enabled=True
            ),
            "default": DataRetentionPolicy(
                retention_days=90,
                compression_enabled=True,
                archive_enabled=True
            )
        })
    
    async def store_event(self, event: Event) -> bool:
        """Store an event in the database"""
        try:
            with storage_request_duration.labels(operation="store").time():
                async with self.db_manager.get_session() as session:
                    # Convert event to dict for storage
                    event_data = event.model_dump()
                    event_data['id'] = str(event.id)
                    event_data["timestamp"] = event.timestamp
                    event_data["type"] = event.type.value
                    event_data["severity"] = event.severity.value
                    
                    # Fix parameter mapping: metadata -> event_metadata
                    event_data["event_metadata"] = event_data.pop("metadata", {})
                    
                    # Store in events table
                    await session.execute(
                        text("""
                        INSERT INTO events (id, type, source, timestamp, severity, data, event_metadata, 
                                          correlation_id, session_id, user_id, tags)
                        VALUES (:id, :type, :source, :timestamp, :severity, :data, :event_metadata,
                                :correlation_id, :session_id, :user_id, :tags)
                        """),
                        event_data
                    )
                    
                    await session.commit()
                    
                    # Update metrics
                    stored_events_total.labels(event_type=event.type.value).inc()
                    storage_requests_total.labels(operation="store", status="success").inc()
                    
                    return True
                    
        except Exception as e:
            logger.error(f"Error storing event: {e}")
            storage_requests_total.labels(operation="store", status="error").inc()
            return False
    
    async def query_events(self, query: StorageQuery) -> List[Event]:
        """Query events from storage"""
        try:
            with storage_request_duration.labels(operation="query").time():
                async with self.db_manager.get_session() as session:
                    # Build query
                    sql_query = "SELECT * FROM events WHERE 1=1"
                    params = {}
                    
                    if query.start_time:
                        sql_query += " AND timestamp >= :start_time"
                        params['start_time'] = query.start_time
                    
                    if query.end_time:
                        sql_query += " AND timestamp <= :end_time"
                        params['end_time'] = query.end_time
                    
                    if query.event_types:
                        sql_query += " AND type = ANY(:event_types)"
                        params['event_types'] = [et.value for et in query.event_types]
                    
                    if query.sources:
                        sql_query += " AND source = ANY(:sources)"
                        params['sources'] = query.sources
                    
                    if query.user_ids:
                        sql_query += " AND user_id = ANY(:user_ids)"
                        params['user_ids'] = query.user_ids
                    
                    sql_query += " ORDER BY timestamp DESC LIMIT :limit OFFSET :offset"
                    params['limit'] = query.limit
                    params['offset'] = query.offset
                    
                    result = await session.execute(text(sql_query), params)
                    rows = result.fetchall()
                    
                    # Convert to Event objects
                    events = []
                    for row in rows:
                        # Convert SQLAlchemy row to dictionary properly (SQLAlchemy 2.0 fix)
                        event_data = dict(row._mapping)
                        event_data['id'] = UUID(str(event_data['id']))
                        
                        # Fix parameter mapping: event_metadata -> metadata
                        if 'event_metadata' in event_data:
                            event_data['metadata'] = event_data.pop('event_metadata', {})
                        
                        events.append(Event(**event_data))
                    
                    storage_requests_total.labels(operation="query", status="success").inc()
                    return events
                    
        except Exception as e:
            logger.error(f"Error querying events: {e}")
            storage_requests_total.labels(operation="query", status="error").inc()
            return []
    
    async def get_storage_stats(self) -> StorageStats:
        """Get storage statistics"""
        try:
            async with self.db_manager.get_session() as session:
                # Get total events
                total_result = await session.execute(text("SELECT COUNT(*) FROM events"))
                total_events = total_result.scalar()
                
                # Get events by type
                type_result = await session.execute(
                    text("SELECT type, COUNT(*) FROM events GROUP BY type")
                )
                events_by_type = {row[0]: row[1] for row in type_result.fetchall()}
                
                # Get events by source
                source_result = await session.execute(
                    text("SELECT source, COUNT(*) FROM events GROUP BY source")
                )
                events_by_source = {row[0]: row[1] for row in source_result.fetchall()}
                
                # Get timestamp range
                time_result = await session.execute(
                    text("SELECT MIN(timestamp), MAX(timestamp) FROM events")
                )
                oldest_event, newest_event = time_result.fetchone()
                
                # Estimate storage size (simplified)
                storage_size_bytes = total_events * 1024  # Rough estimate
                
                return StorageStats(
                    total_events=total_events,
                    events_by_type=events_by_type,
                    events_by_source=events_by_source,
                    storage_size_bytes=storage_size_bytes,
                    oldest_event=oldest_event,
                    newest_event=newest_event
                )
                
        except Exception as e:
            logger.error(f"Error getting storage stats: {e}")
            return StorageStats(
                total_events=0,
                events_by_type={},
                events_by_source={},
                storage_size_bytes=0,
                oldest_event=None,
                newest_event=None
            )
    
    async def cleanup_old_data(self) -> Dict[str, int]:
        """Clean up old data based on retention policies"""
        cleanup_stats = {}
        
        try:
            for event_type, policy in self.retention_policies.items():
                if event_type == "default":
                    continue
                    
                cutoff_date = datetime.now() - timedelta(days=policy.retention_days)
                
                async with self.db_manager.get_session() as session:
                    # Count events to be deleted
                    count_result = await session.execute(
                        text("SELECT COUNT(*) FROM events WHERE type = :type AND timestamp < :cutoff"),
                        {"type": event_type, "cutoff": cutoff_date}
                    )
                    count = count_result.scalar()
                    
                    if count > 0:
                        # Delete old events
                        await session.execute(
                            text("DELETE FROM events WHERE type = :type AND timestamp < :cutoff"),
                            {"type": event_type, "cutoff": cutoff_date}
                        )
                        await session.commit()
                        
                        cleanup_stats[event_type] = count
                        data_retention_operations.labels(operation="cleanup").inc()
                        
                        logger.info(f"Cleaned up {count} old events of type {event_type}")
            
            return cleanup_stats
            
        except Exception as e:
            logger.error(f"Error during cleanup: {e}")
            return cleanup_stats
    
    async def backup_data(self, backup_path: str) -> bool:
        """Backup data to specified path"""
        try:
            # This is a simplified backup implementation
            # In production, you'd use proper backup tools
            async with self.db_manager.get_session() as session:
                result = await session.execute(text("SELECT * FROM events"))
                events = result.fetchall()
                
                # Save to backup file (JSON format)
                import json
                backup_data = []
                for event in events:
                    event_dict = dict(event)
                    event_dict['timestamp'] = event_dict['timestamp'].isoformat()
                    backup_data.append(event_dict)
                
                # Use synchronous file I/O for backup (acceptable for backup operations)
                with open(backup_path, 'w') as f:
                    json.dump(backup_data, f, indent=2)
                
                logger.info(f"Backed up {len(events)} events to {backup_path}")
                return True
                
        except Exception as e:
            logger.error(f"Error during backup: {e}")
            return False


# Initialize storage service
storage_service = None


def get_storage_service() -> StorageService:
    """Get storage service instance"""
    global storage_service
    if storage_service is None:
        storage_service = StorageService(db_manager, message_broker)
    return storage_service


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    global db_manager, message_broker
    
    # Startup
    logger.info("Starting Data Storage Service...")
    
    # Initialize database
    db_manager = DatabaseManager(settings)
    await db_manager.initialize()
    
    # Initialize message broker
    message_broker = MessageBroker(settings)
    await message_broker.connect()
    
    # Create tables if they don't exist
    await create_tables()
    
    # Start background tasks
    cleanup_task_handle = asyncio.create_task(cleanup_task())
    
    # Start consuming events from message broker
    storage_service_instance = get_storage_service()
    consumer_task = asyncio.create_task(start_event_consumer(storage_service_instance))
    
    logger.info("Data Storage Service started successfully!")
    
    yield
    
    # Shutdown
    logger.info("Shutting down Data Storage Service...")
    if message_broker:
        await message_broker.close()
    if db_manager:
        await db_manager.close()


async def create_tables():
    """Create database tables"""
    try:
        async with db_manager.get_session() as session:
            await session.execute(text("""
                CREATE TABLE IF NOT EXISTS events (
                    id UUID PRIMARY KEY,
                    type VARCHAR(50) NOT NULL,
                    source VARCHAR(100) NOT NULL,
                    timestamp TIMESTAMP NOT NULL,
                    severity VARCHAR(20) NOT NULL,
                    data JSONB,
                    event_metadata JSONB,
                    correlation_id VARCHAR(100),
                    session_id VARCHAR(100),
                    user_id VARCHAR(100),
                    tags TEXT[],
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """))
            
            # Create indexes for better query performance
            await session.execute(text("CREATE INDEX IF NOT EXISTS idx_events_timestamp ON events(timestamp)"))
            await session.execute(text("CREATE INDEX IF NOT EXISTS idx_events_type ON events(type)"))
            await session.execute(text("CREATE INDEX IF NOT EXISTS idx_events_source ON events(source)"))
            await session.execute(text("CREATE INDEX IF NOT EXISTS idx_events_user_id ON events(user_id)"))
            
            await session.commit()
            logger.info("Database tables created successfully")
            
    except Exception as e:
        logger.error(f"Error creating tables: {e}")


async def cleanup_task():
    """Background task for data cleanup"""
    while True:
        try:
            await asyncio.sleep(3600)  # Run every hour
            service = get_storage_service()
            await service.cleanup_old_data()
        except Exception as e:
            logger.error(f"Error in cleanup task: {e}")


async def start_event_consumer(storage_service_instance: StorageService):
    """Start consuming events from message broker"""
    try:
        logger.info("Starting event consumer...")
        
        # Declare queue and bind to events exchange
        queue = await message_broker.declare_queue(
            queue_name="storage.events",
            routing_key="events.#",
            exchange_name="events",
            durable=True
        )
        
        async def process_event(envelope):
            """Process received event"""
            try:
                # Extract event data from envelope payload
                event_data = envelope.payload
                logger.info(f"Processing event: {event_data.get('id', 'unknown')}")
                
                # Convert dict to Event object
                event = Event(**event_data)
                
                # Store the event
                success = await storage_service_instance.store_event(event)
                if success:
                    logger.info(f"Successfully stored event: {event.id}")
                else:
                    logger.error(f"Failed to store event: {event.id}")
                    
            except Exception as e:
                logger.error(f"Error processing event: {e}")
        
        # Start consuming messages
        await message_broker.consume(
            queue_name="storage.events",
            callback=process_event,
            auto_ack=False
        )
        logger.info("Event consumer started successfully")
        
    except Exception as e:
        logger.error(f"Error starting event consumer: {e}")


# Create FastAPI app
app = FastAPI(
    title="StreamFlow Data Storage Service",
    description="Data storage and retrieval service for StreamFlow analytics pipeline",
    version="1.0.0",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.post("/api/v1/events", response_model=Dict[str, Any])
async def store_event(
    event: Event,
    background_tasks: BackgroundTasks,
    service: StorageService = Depends(get_storage_service)
):
    """Store an event"""
    success = await service.store_event(event)
    
    if success:
        return {"status": "success", "message": "Event stored successfully"}
    else:
        raise HTTPException(status_code=500, detail="Failed to store event")


@app.post("/api/v1/events/query", response_model=List[Event])
async def query_events(
    query: StorageQuery,
    service: StorageService = Depends(get_storage_service)
):
    """Query events from storage"""
    events = await service.query_events(query)
    return events


@app.get("/api/v1/stats", response_model=StorageStats)
async def get_storage_stats(service: StorageService = Depends(get_storage_service)):
    """Get storage statistics"""
    stats = await service.get_storage_stats()
    return stats


@app.post("/api/v1/cleanup")
async def cleanup_old_data(
    background_tasks: BackgroundTasks,
    service: StorageService = Depends(get_storage_service)
):
    """Trigger data cleanup"""
    cleanup_stats = await service.cleanup_old_data()
    return {"status": "success", "cleaned_up": cleanup_stats}


@app.post("/api/v1/backup")
async def backup_data(
    backup_path: str = Query(..., description="Path to backup file"),
    service: StorageService = Depends(get_storage_service)
):
    """Backup data"""
    success = await service.backup_data(backup_path)
    
    if success:
        return {"status": "success", "message": f"Data backed up to {backup_path}"}
    else:
        raise HTTPException(status_code=500, detail="Backup failed")


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    try:
        # Check database connection
        async with db_manager.get_session() as session:
            await session.execute(text("SELECT 1"))
        
        return {
            "status": "healthy",
            "service": "storage",
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "service": "storage",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }


@app.get("/ready")
async def readiness_check():
    """Readiness check endpoint"""
    return {"status": "ready", "service": "storage"}


@app.get("/metrics")
async def get_metrics():
    """Prometheus metrics endpoint"""
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8004,
        reload=True,
        log_level="info"
    )
