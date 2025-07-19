"""
Database utilities with async SQLAlchemy support
StreamFlow - real-time analytics pipeline

 
"""
import logging
from contextlib import asynccontextmanager
from typing import Any, Dict, List, Optional, Type, TypeVar, AsyncGenerator
from uuid import UUID
from datetime import datetime

from sqlalchemy import create_engine, MetaData, Table, Column, String, DateTime, JSON, Boolean, Integer, Float, Text, func
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from sqlalchemy.sql import select, insert, update, delete
from sqlalchemy.dialects.postgresql import UUID as SQLAlchemyUUID

from .config import Settings, get_settings

logger = logging.getLogger(__name__)

# Create base class for models
Base = declarative_base()

# Type variable for generic operations
T = TypeVar('T')


class DatabaseManager:
    """Async database manager with connection pooling"""
    
    def __init__(self, settings: Optional[Settings] = None):
        self.settings = settings or get_settings()
        self.engine = None
        self.session_factory = None
        self.metadata = MetaData()
        
    async def initialize(self):
        """Initialize database connection and session factory"""
        try:
            self.engine = create_async_engine(
                self.settings.database.url,
                echo=self.settings.database.echo,
                pool_size=self.settings.database.pool_size,
                max_overflow=self.settings.database.max_overflow,
                pool_pre_ping=True,
                pool_recycle=3600,
            )
            
            self.session_factory = async_sessionmaker(
                self.engine,
                class_=AsyncSession,
                expire_on_commit=False
            )
            
            logger.info("Database initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize database: {e}")
            raise
    
    async def close(self):
        """Close database connections"""
        if self.engine:
            await self.engine.dispose()
            logger.info("Database connections closed")
    
    @asynccontextmanager
    async def get_session(self) -> AsyncSession:
        """Get database session with automatic cleanup"""
        if not self.session_factory:
            await self.initialize()
        
        session = self.session_factory()
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
    
    async def create_tables(self):
        """Create all tables"""
        if not self.engine:
            await self.initialize()
        
        async with self.engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        
        logger.info("Database tables created")
    
    async def drop_tables(self):
        """Drop all tables"""
        if not self.engine:
            await self.initialize()
        
        async with self.engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)
        
        logger.info("Database tables dropped")
    
    async def execute_query(self, query: str, params: Optional[Dict[str, Any]] = None) -> Any:
        """Execute raw SQL query"""
        async with self.get_session() as session:
            result = await session.execute(query, params or {})
            await session.commit()
            return result
    
    async def health_check(self) -> Dict[str, Any]:
        """Database health check"""
        try:
            async with self.get_session() as session:
                await session.execute(select(1))
                return {
                    "status": "healthy",
                    "database": "postgresql",
                    "connection_pool": {
                        "size": self.engine.pool.size(),
                        "checked_in": self.engine.pool.checkedin(),
                        "checked_out": self.engine.pool.checkedout(),
                        "overflow": self.engine.pool.overflow(),
                        "invalid": self.engine.pool.invalid()
                    }
                }
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e)
            }


class BaseRepository:
    """Base repository class for CRUD operations"""
    
    def __init__(self, model: Type[T], db_manager: DatabaseManager):
        self.model = model
        self.db_manager = db_manager
    
    async def create(self, **kwargs) -> T:
        """Create new record"""
        async with self.db_manager.get_session() as session:
            instance = self.model(**kwargs)
            session.add(instance)
            await session.commit()
            await session.refresh(instance)
            return instance
    
    async def get_by_id(self, id: UUID) -> Optional[T]:
        """Get record by ID"""
        async with self.db_manager.get_session() as session:
            result = await session.execute(
                select(self.model).where(self.model.id == id)
            )
            return result.scalar_one_or_none()
    
    async def get_by_filter(self, **filters) -> List[T]:
        """Get records by filter"""
        async with self.db_manager.get_session() as session:
            query = select(self.model)
            for field, value in filters.items():
                if hasattr(self.model, field):
                    query = query.where(getattr(self.model, field) == value)
            
            result = await session.execute(query)
            return result.scalars().all()
    
    async def update(self, id: UUID, **kwargs) -> Optional[T]:
        """Update record by ID"""
        async with self.db_manager.get_session() as session:
            instance = await session.get(self.model, id)
            if not instance:
                return None
            
            for field, value in kwargs.items():
                if hasattr(instance, field):
                    setattr(instance, field, value)
            
            await session.commit()
            await session.refresh(instance)
            return instance
    
    async def delete(self, id: UUID) -> bool:
        """Delete record by ID"""
        async with self.db_manager.get_session() as session:
            instance = await session.get(self.model, id)
            if not instance:
                return False
            
            await session.delete(instance)
            await session.commit()
            return True
    
    async def list_paginated(
        self,
        page: int = 1,
        page_size: int = 100,
        filters: Optional[Dict[str, Any]] = None,
        sort_by: Optional[str] = None,
        sort_order: str = "desc"
    ) -> Dict[str, Any]:
        """List records with pagination"""
        async with self.db_manager.get_session() as session:
            query = select(self.model)
            
            # Apply filters
            if filters:
                for field, value in filters.items():
                    if hasattr(self.model, field):
                        query = query.where(getattr(self.model, field) == value)
            
            # Apply sorting
            if sort_by and hasattr(self.model, sort_by):
                sort_column = getattr(self.model, sort_by)
                if sort_order.lower() == "asc":
                    query = query.order_by(sort_column.asc())
                else:
                    query = query.order_by(sort_column.desc())
            
            # Count total records
            count_query = select(func.count()).select_from(query.subquery())
            total_result = await session.execute(count_query)
            total = total_result.scalar()
            
            # Apply pagination
            offset = (page - 1) * page_size
            query = query.offset(offset).limit(page_size)
            
            result = await session.execute(query)
            records = result.scalars().all()
            
            return {
                "data": records,
                "pagination": {
                    "page": page,
                    "page_size": page_size,
                    "total": total,
                    "pages": (total + page_size - 1) // page_size,
                    "has_next": page * page_size < total,
                    "has_prev": page > 1
                }
            }
    
    async def count(self, filters: Optional[Dict[str, Any]] = None) -> int:
        """Count records"""
        async with self.db_manager.get_session() as session:
            query = select(func.count(self.model.id))
            
            if filters:
                for field, value in filters.items():
                    if hasattr(self.model, field):
                        query = query.where(getattr(self.model, field) == value)
            
            result = await session.execute(query)
            return result.scalar()
    
    async def exists(self, **filters) -> bool:
        """Check if record exists"""
        count = await self.count(filters)
        return count > 0


# Database models
class EventModel(Base):
    """Event database model"""
    __tablename__ = "events"
    
    id = Column(SQLAlchemyUUID(as_uuid=True), primary_key=True)
    type = Column(String(100), nullable=False, index=True)
    source = Column(String(255), nullable=False, index=True)
    timestamp = Column(DateTime, nullable=False, index=True)
    severity = Column(String(50), nullable=False)
    data = Column(JSON, nullable=False)
    event_metadata = Column(JSON, nullable=False)
    correlation_id = Column(String(255), nullable=True, index=True)
    session_id = Column(String(255), nullable=True, index=True)
    user_id = Column(String(255), nullable=True, index=True)
    tags = Column(JSON, nullable=False)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    processed_at = Column(DateTime, nullable=True)
    processed = Column(Boolean, default=False, index=True)


class AlertRuleModel(Base):
    """Alert rule database model"""
    __tablename__ = "alert_rules"
    
    id = Column(SQLAlchemyUUID(as_uuid=True), primary_key=True)
    name = Column(String(255), nullable=False, unique=True)
    description = Column(Text, nullable=True)
    condition = Column(Text, nullable=False)
    threshold = Column(Float, nullable=False)
    window = Column(String(50), nullable=False)
    level = Column(String(50), nullable=False)
    channels = Column(JSON, nullable=False)
    enabled = Column(Boolean, default=True, index=True)
    suppression_minutes = Column(Integer, default=0)
    escalation_minutes = Column(Integer, default=0)
    tags = Column(JSON, nullable=False)
    rule_metadata = Column(JSON, nullable=False)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow)


class AlertModel(Base):
    """Alert database model"""
    __tablename__ = "alerts"
    
    id = Column(SQLAlchemyUUID(as_uuid=True), primary_key=True)
    rule_id = Column(SQLAlchemyUUID(as_uuid=True), nullable=False, index=True)
    level = Column(String(50), nullable=False, index=True)
    title = Column(String(255), nullable=False)
    message = Column(Text, nullable=False)
    timestamp = Column(DateTime, nullable=False, index=True)
    resolved = Column(Boolean, default=False, index=True)
    resolved_at = Column(DateTime, nullable=True)
    resolved_by = Column(String(255), nullable=True)
    acknowledged = Column(Boolean, default=False, index=True)
    acknowledged_at = Column(DateTime, nullable=True)
    acknowledged_by = Column(String(255), nullable=True)
    data = Column(JSON, nullable=False)
    alert_metadata = Column(JSON, nullable=False)


class MetricModel(Base):
    """Metric database model"""
    __tablename__ = "metrics"
    
    id = Column(SQLAlchemyUUID(as_uuid=True), primary_key=True)
    name = Column(String(255), nullable=False, index=True)
    type = Column(String(50), nullable=False)
    value = Column(Float, nullable=False)
    timestamp = Column(DateTime, nullable=False, index=True)
    tags = Column(JSON, nullable=False)
    metric_metadata = Column(JSON, nullable=False)


# Global instances
_db_manager: Optional[DatabaseManager] = None


async def get_database_manager() -> DatabaseManager:
    """Get global database manager instance"""
    global _db_manager
    if _db_manager is None:
        _db_manager = DatabaseManager()
        await _db_manager.initialize()
    return _db_manager


async def cleanup_database():
    """Cleanup global database resources"""
    global _db_manager
    if _db_manager:
        await _db_manager.close()
        _db_manager = None
