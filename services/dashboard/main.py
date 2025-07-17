"""Dashboard service main application."""

import os
from pathlib import Path
from typing import Dict, List

from fastapi import FastAPI, Request, Depends, HTTPException, status
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.security import HTTPBearer
import uvicorn

from shared.utils.config import get_settings
from shared.utils.logging import setup_logging, get_logger
from shared.models.auth import User
from shared.models.metrics import Dashboard, Widget, MetricQueryResult
from shared.models.alerts import Alert, AlertRule
from shared.models.events import Event

from .api import dashboards, metrics, alerts, auth
from .websocket import websocket_manager
from .auth import get_current_user

# Setup logging
setup_logging()
logger = get_logger(__name__)

# Get settings
settings = get_settings()

# Initialize FastAPI app
app = FastAPI(
    title=settings.ui_title,
    description=settings.ui_description,
    version=settings.ui_version,
    docs_url="/docs" if settings.debug else None,
    redoc_url="/redoc" if settings.debug else None,
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Trusted host middleware for production
if not settings.debug:
    app.add_middleware(
        TrustedHostMiddleware,
        allowed_hosts=["localhost", "127.0.0.1", "*.streamflow.dev"]
    )

# Static files and templates
current_dir = Path(__file__).parent
static_dir = current_dir.parent.parent / "ui" / "static"
templates_dir = current_dir.parent.parent / "ui" / "templates"

# Create directories if they don't exist
static_dir.mkdir(parents=True, exist_ok=True)
templates_dir.mkdir(parents=True, exist_ok=True)

app.mount("/static", StaticFiles(directory=static_dir), name="static")
templates = Jinja2Templates(directory=templates_dir)

# Include API routers
app.include_router(auth.router, prefix="/api/v1/auth", tags=["Authentication"])
app.include_router(dashboards.router, prefix="/api/v1/dashboards", tags=["Dashboards"])
app.include_router(metrics.router, prefix="/api/v1/metrics", tags=["Metrics"])
app.include_router(alerts.router, prefix="/api/v1/alerts", tags=["Alerts"])

# Include WebSocket endpoint
app.include_router(websocket_manager.router, prefix="/ws")


@app.get("/", response_class=HTMLResponse)
async def dashboard_home(request: Request):
    """Main dashboard page."""
    return templates.TemplateResponse(
        "dashboard.html",
        {
            "request": request,
            "title": settings.ui_title,
            "theme": settings.ui_theme,
            "version": settings.ui_version,
        }
    )


@app.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    """Login page."""
    return templates.TemplateResponse(
        "login.html",
        {
            "request": request,
            "title": f"Login - {settings.ui_title}",
        }
    )


@app.get("/alerts", response_class=HTMLResponse)
async def alerts_page(request: Request, current_user: User = Depends(get_current_user)):
    """Alerts management page."""
    return templates.TemplateResponse(
        "alerts.html",
        {
            "request": request,
            "title": f"Alerts - {settings.ui_title}",
            "user": current_user,
        }
    )


@app.get("/metrics", response_class=HTMLResponse)
async def metrics_page(request: Request, current_user: User = Depends(get_current_user)):
    """Metrics visualization page."""
    return templates.TemplateResponse(
        "metrics.html",
        {
            "request": request,
            "title": f"Metrics - {settings.ui_title}",
            "user": current_user,
        }
    )


@app.get("/events", response_class=HTMLResponse)
async def events_page(request: Request, current_user: User = Depends(get_current_user)):
    """Events monitoring page."""
    return templates.TemplateResponse(
        "events.html",
        {
            "request": request,
            "title": f"Events - {settings.ui_title}",
            "user": current_user,
        }
    )


@app.get("/settings", response_class=HTMLResponse)
async def settings_page(request: Request, current_user: User = Depends(get_current_user)):
    """Settings page."""
    return templates.TemplateResponse(
        "settings.html",
        {
            "request": request,
            "title": f"Settings - {settings.ui_title}",
            "user": current_user,
        }
    )


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "dashboard",
        "version": settings.ui_version,
        "timestamp": "2024-01-01T00:00:00Z"
    }


@app.get("/ready")
async def readiness_check():
    """Readiness check endpoint."""
    # Add actual readiness checks here (database, Redis, etc.)
    return {
        "status": "ready",
        "service": "dashboard",
        "checks": {
            "database": "healthy",
            "redis": "healthy",
            "rabbitmq": "healthy"
        }
    }


@app.on_event("startup")
async def startup_event():
    """Application startup event."""
    logger.info("Starting StreamFlow Dashboard Service")
    logger.info(f"Environment: {settings.environment}")
    logger.info(f"Debug mode: {settings.debug}")


@app.on_event("shutdown")
async def shutdown_event():
    """Application shutdown event."""
    logger.info("Shutting down StreamFlow Dashboard Service")


if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host=settings.api_host,
        port=settings.dashboard_port,
        reload=settings.debug,
        log_level=settings.log_level.lower(),
    )