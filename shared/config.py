"""
Configuration management using Pydantic Settings
StreamFlow - real-time analytics pipeline

 
"""
import os
from typing import List, Optional
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings


class RabbitMQSettings(BaseSettings):
    """RabbitMQ configuration"""
    url: str = Field(default="amqp://guest:guest@localhost:5672/", env="RABBITMQ_URL")
    exchange_events: str = Field(default="events", env="RABBITMQ_EXCHANGE_EVENTS")
    exchange_analytics: str = Field(default="analytics", env="RABBITMQ_EXCHANGE_ANALYTICS")
    exchange_alerts: str = Field(default="alerts", env="RABBITMQ_EXCHANGE_ALERTS")
    max_connections: int = Field(default=10, env="RABBITMQ_MAX_CONNECTIONS")
    heartbeat: int = Field(default=600, env="RABBITMQ_HEARTBEAT")
    
    class Config:
        env_prefix = "RABBITMQ_"


class DatabaseSettings(BaseSettings):
    """Database configuration"""
    url: str = Field(default="postgresql+asyncpg://user:pass@localhost/streamflow", env="DATABASE_URL")
    echo: bool = Field(default=False, env="DATABASE_ECHO")
    pool_size: int = Field(default=5, env="DATABASE_POOL_SIZE")
    max_overflow: int = Field(default=10, env="DATABASE_MAX_OVERFLOW")
    
    class Config:
        env_prefix = "DATABASE_"


class RedisSettings(BaseSettings):
    """Redis configuration"""
    url: str = Field(default="redis://localhost:6379", env="REDIS_URL")
    db: int = Field(default=0, env="REDIS_DB")
    max_connections: int = Field(default=10, env="REDIS_MAX_CONNECTIONS")
    
    class Config:
        env_prefix = "REDIS_"


class SecuritySettings(BaseSettings):
    """Security configuration"""
    jwt_secret_key: str = Field(env="JWT_SECRET_KEY")
    jwt_algorithm: str = Field(default="HS256", env="JWT_ALGORITHM")
    jwt_expire_minutes: int = Field(default=30, env="JWT_EXPIRE_MINUTES")
    bcrypt_rounds: int = Field(default=12, env="BCRYPT_ROUNDS")
    
    @field_validator("jwt_secret_key")
    @classmethod
    def validate_jwt_secret(cls, v):
        if not v:
            raise ValueError("JWT_SECRET_KEY is required")
        if len(v) < 32:
            raise ValueError("JWT_SECRET_KEY must be at least 32 characters")
        return v


class ServiceSettings(BaseSettings):
    """Service-specific configuration"""
    ingestion_port: int = Field(default=8001, env="INGESTION_PORT")
    analytics_port: int = Field(default=8002, env="ANALYTICS_PORT")
    alerting_port: int = Field(default=8003, env="ALERTING_PORT")
    dashboard_port: int = Field(default=8004, env="DASHBOARD_PORT")
    storage_port: int = Field(default=8005, env="STORAGE_PORT")
    
    # Service URLs for inter-service communication
    ingestion_url: str = Field(default="http://localhost:8001", env="INGESTION_URL")
    analytics_url: str = Field(default="http://localhost:8002", env="ANALYTICS_URL")
    alerting_url: str = Field(default="http://localhost:8003", env="ALERTING_URL")
    dashboard_url: str = Field(default="http://localhost:8004", env="DASHBOARD_URL")
    storage_url: str = Field(default="http://localhost:8005", env="STORAGE_URL")


class MonitoringSettings(BaseSettings):
    """Monitoring and observability configuration"""
    prometheus_enabled: bool = Field(default=True, env="PROMETHEUS_ENABLED")
    prometheus_port: int = Field(default=8080, env="PROMETHEUS_PORT")
    jaeger_enabled: bool = Field(default=False, env="JAEGER_ENABLED")
    jaeger_endpoint: Optional[str] = Field(default=None, env="JAEGER_ENDPOINT")
    log_level: str = Field(default="INFO", env="LOG_LEVEL")
    log_format: str = Field(default="json", env="LOG_FORMAT")
    
    class Config:
        env_prefix = "MONITORING_"


class RateLimitSettings(BaseSettings):
    """Rate limiting configuration"""
    enabled: bool = Field(default=True, env="RATE_LIMIT_ENABLED")
    requests_per_minute: int = Field(default=100, env="RATE_LIMIT_REQUESTS_PER_MINUTE")
    burst_size: int = Field(default=10, env="RATE_LIMIT_BURST_SIZE")
    
    class Config:
        env_prefix = "RATE_LIMIT_"


class Settings(BaseSettings):
    """Main application settings"""
    
    # Environment
    environment: str = Field(default="development", env="ENVIRONMENT")
    debug: bool = Field(default=False, env="DEBUG")
    
    # Application
    app_name: str = Field(default="StreamFlow", env="APP_NAME")
    app_version: str = Field(default="0.1.0", env="APP_VERSION")
    
    # CORS
    cors_origins: List[str] = Field(default=["*"], env="CORS_ORIGINS")
    
    # Nested settings
    rabbitmq: RabbitMQSettings = Field(default_factory=RabbitMQSettings)
    database: DatabaseSettings = Field(default_factory=DatabaseSettings)
    redis: RedisSettings = Field(default_factory=RedisSettings)
    security: SecuritySettings = Field(default_factory=SecuritySettings)
    services: ServiceSettings = Field(default_factory=ServiceSettings)
    monitoring: MonitoringSettings = Field(default_factory=MonitoringSettings)
    rate_limit: RateLimitSettings = Field(default_factory=RateLimitSettings)
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False
        extra = "ignore"
    
    @field_validator("environment")
    @classmethod
    def validate_environment(cls, v):
        if v not in ["development", "staging", "production"]:
            raise ValueError("Environment must be one of: development, staging, production")
        return v
    
    @field_validator("cors_origins", mode="before")
    @classmethod
    def parse_cors_origins(cls, v):
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(",")]
        return v


# Global settings instance (lazy loaded)
_settings = None


def get_settings() -> Settings:
    """Get application settings"""
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings


def reload_settings():
    """Reload settings from environment"""
    global _settings
    _settings = None
    return get_settings()
