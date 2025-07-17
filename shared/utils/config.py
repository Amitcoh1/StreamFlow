"""Configuration management for StreamFlow."""

from functools import lru_cache
from typing import List, Optional

from pydantic import BaseSettings, Field


class Settings(BaseSettings):
    """Application settings."""
    
    # Application
    app_name: str = "StreamFlow"
    app_version: str = "1.0.0"
    debug: bool = False
    environment: str = Field(default="development", description="Environment: development, staging, production")
    
    # API Configuration
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    api_prefix: str = "/api/v1"
    cors_origins: List[str] = ["*"]
    
    # Database
    database_url: str = Field(..., description="Database URL")
    database_pool_size: int = 10
    database_max_overflow: int = 20
    database_echo: bool = False
    
    # Redis
    redis_url: str = Field(default="redis://localhost:6379", description="Redis URL")
    redis_max_connections: int = 10
    
    # RabbitMQ
    rabbitmq_url: str = Field(default="amqp://guest:guest@localhost:5672/", description="RabbitMQ URL")
    rabbitmq_exchange_events: str = "events"
    rabbitmq_exchange_analytics: str = "analytics"
    rabbitmq_exchange_alerts: str = "alerts"
    rabbitmq_queue_ingestion: str = "ingestion"
    rabbitmq_queue_analytics: str = "analytics"
    rabbitmq_queue_alerts: str = "alerts"
    
    # JWT Authentication
    jwt_secret_key: str = Field(..., description="JWT secret key")
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 30
    jwt_refresh_expire_days: int = 7
    
    # Security
    password_min_length: int = 8
    rate_limit_requests: int = 100
    rate_limit_period: int = 60  # seconds
    
    # Services Configuration
    ingestion_port: int = 8001
    analytics_port: int = 8002
    alerting_port: int = 8003
    dashboard_port: int = 8004
    storage_port: int = 8005
    
    # Monitoring
    metrics_enabled: bool = True
    metrics_port: int = 9090
    health_check_interval: int = 30
    
    # Logging
    log_level: str = "INFO"
    log_format: str = "json"
    log_file: Optional[str] = None
    
    # Data Processing
    batch_size: int = 1000
    processing_timeout: int = 30
    max_retries: int = 3
    
    # Alert Configuration
    alert_evaluation_interval: int = 60  # seconds
    alert_max_notifications_per_hour: int = 10
    
    # UI Configuration
    ui_title: str = "StreamFlow Dashboard"
    ui_description: str = "Real-time Analytics Pipeline"
    ui_version: str = "1.0.0"
    ui_theme: str = "dark"
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


@lru_cache()
def get_settings() -> Settings:
    """Get application settings (cached)."""
    return Settings()


def get_database_url() -> str:
    """Get database URL from settings."""
    settings = get_settings()
    return settings.database_url


def get_redis_url() -> str:
    """Get Redis URL from settings."""
    settings = get_settings()
    return settings.redis_url


def get_rabbitmq_url() -> str:
    """Get RabbitMQ URL from settings."""
    settings = get_settings()
    return settings.rabbitmq_url


def is_production() -> bool:
    """Check if running in production environment."""
    settings = get_settings()
    return settings.environment.lower() == "production"


def is_development() -> bool:
    """Check if running in development environment."""
    settings = get_settings()
    return settings.environment.lower() == "development"