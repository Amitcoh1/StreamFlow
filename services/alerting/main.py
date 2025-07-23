"""
Alert Engine Service - Rule-based alerting with multiple notification channels
StreamFlow - real-time analytics pipeline

 
"""
import asyncio
import logging
from abc import ABC, abstractmethod
from contextlib import asynccontextmanager
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Union
from enum import Enum
from dataclasses import dataclass, field
from uuid import UUID, uuid4

from fastapi import FastAPI, HTTPException, Depends, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
import uvicorn
from sqlalchemy import text

from streamflow.shared.config import get_settings
from streamflow.shared.models import (
    Event, AlertRule, Alert, AlertLevel, AlertChannel, 
    MessageEnvelope, HealthCheck, HealthStatus, APIResponse
)
from streamflow.shared.messaging import get_message_broker, get_event_publisher
from streamflow.shared.database import get_database_manager

logger = logging.getLogger(__name__)

# Global state
settings = get_settings()
security = HTTPBearer()


class AlertState(Enum):
    """Alert states"""
    PENDING = "pending"
    ACTIVE = "active"
    SUPPRESSED = "suppressed"
    RESOLVED = "resolved"
    ESCALATED = "escalated"


@dataclass
class AlertContext:
    """Alert context with rule and event data"""
    rule: AlertRule
    event: Event
    value: float
    threshold: float
    window_data: List[Event] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


class NotificationChannel(ABC):
    """Abstract base class for notification channels"""
    
    @abstractmethod
    async def send(self, alert: Alert, context: AlertContext) -> bool:
        """Send alert notification"""
        pass
    
    @abstractmethod
    async def is_available(self) -> bool:
        """Check if channel is available"""
        pass


class EmailNotificationChannel(NotificationChannel):
    """Email notification channel"""
    
    def __init__(self, smtp_config: Dict[str, Any]):
        self.smtp_config = smtp_config
    
    async def send(self, alert: Alert, context: AlertContext) -> bool:
        """Send email notification"""
        try:
            # In production, integrate with actual email service
            logger.info(f"Sending email alert: {alert.title}")
            logger.info(f"To: {self.smtp_config.get('recipients', [])}")
            logger.info(f"Subject: {alert.title}")
            logger.info(f"Message: {alert.message}")
            
            # Simulate email sending
            await asyncio.sleep(0.1)
            return True
            
        except Exception as e:
            logger.error(f"Failed to send email alert: {e}")
            return False
    
    async def is_available(self) -> bool:
        """Check if email service is available"""
        return True  # Simplified for demo


class SlackNotificationChannel(NotificationChannel):
    """Slack notification channel"""
    
    def __init__(self, webhook_url: str):
        self.webhook_url = webhook_url
    
    async def send(self, alert: Alert, context: AlertContext) -> bool:
        """Send Slack notification"""
        try:
            # In production, use actual Slack webhook
            logger.info(f"Sending Slack alert: {alert.title}")
            logger.info(f"Webhook: {self.webhook_url}")
            
            slack_payload = {
                "text": alert.title,
                "attachments": [{
                    "color": self._get_color_for_level(alert.level),
                    "fields": [
                        {"title": "Level", "value": alert.level.value, "short": True},
                        {"title": "Rule", "value": context.rule.name, "short": True},
                        {"title": "Value", "value": str(context.value), "short": True},
                        {"title": "Threshold", "value": str(context.threshold), "short": True},
                    ]
                }]
            }
            
            # Simulate Slack sending
            await asyncio.sleep(0.1)
            return True
            
        except Exception as e:
            logger.error(f"Failed to send Slack alert: {e}")
            return False
    
    def _get_color_for_level(self, level: AlertLevel) -> str:
        """Get color for alert level"""
        colors = {
            AlertLevel.INFO: "good",
            AlertLevel.WARNING: "warning",
            AlertLevel.ERROR: "danger",
            AlertLevel.CRITICAL: "danger"
        }
        return colors.get(level, "warning")
    
    async def is_available(self) -> bool:
        """Check if Slack webhook is available"""
        return True  # Simplified for demo


class WebhookNotificationChannel(NotificationChannel):
    """Webhook notification channel"""
    
    def __init__(self, webhook_url: str, headers: Optional[Dict[str, str]] = None):
        self.webhook_url = webhook_url
        self.headers = headers or {}
    
    async def send(self, alert: Alert, context: AlertContext) -> bool:
        """Send webhook notification"""
        try:
            # In production, use actual HTTP client
            logger.info(f"Sending webhook alert: {alert.title}")
            logger.info(f"URL: {self.webhook_url}")
            
            payload = {
                "alert": {
                    "id": str(alert.id),
                    "title": alert.title,
                    "message": alert.message,
                    "level": alert.level.value,
                    "timestamp": alert.timestamp.isoformat(),
                },
                "rule": {
                    "id": str(context.rule.id),
                    "name": context.rule.name,
                    "condition": context.rule.condition,
                },
                "context": {
                    "value": context.value,
                    "threshold": context.threshold,
                    "event_id": str(context.event.id),
                }
            }
            
            # Simulate webhook sending
            await asyncio.sleep(0.1)
            return True
            
        except Exception as e:
            logger.error(f"Failed to send webhook alert: {e}")
            return False
    
    async def is_available(self) -> bool:
        """Check if webhook endpoint is available"""
        return True  # Simplified for demo


class AlertEngine:
    """Main alert engine with rule management and notification"""
    
    def __init__(self):
        self.settings = get_settings()
        self.rules: Dict[UUID, AlertRule] = {}
        self.active_alerts: Dict[UUID, Alert] = {}
        self.alert_states: Dict[UUID, AlertState] = {}
        self.notification_channels: Dict[AlertChannel, NotificationChannel] = {}
        self.is_running = False
        self._setup_notification_channels()
    
    def _setup_notification_channels(self):
        """Setup notification channels"""
        # Email channel
        email_config = {
            "smtp_host": "smtp.gmail.com",
            "smtp_port": 587,
            "username": "alerts@streamflow.dev",
            "password": "app_password",
            "recipients": ["admin@streamflow.dev"]
        }
        self.notification_channels[AlertChannel.EMAIL] = EmailNotificationChannel(email_config)
        
        # Slack channel
        slack_webhook = "https://hooks.slack.com/services/YOUR/SLACK/WEBHOOK"
        self.notification_channels[AlertChannel.SLACK] = SlackNotificationChannel(slack_webhook)
        
        # Webhook channel
        webhook_url = "https://api.example.com/alerts"
        self.notification_channels[AlertChannel.WEBHOOK] = WebhookNotificationChannel(webhook_url)
    
    async def start(self):
        """Start alert engine"""
        if self.is_running:
            return
        
        self.is_running = True
        logger.info("Starting Alert Engine...")
        
        # Initialize message broker
        broker = await get_message_broker()
        
        # Setup alert queue for analytics results
        await broker.declare_queue(
            "alerting.analytics",
            "analytics.*",
            self.settings.rabbitmq.exchange_analytics
        )
        
        # Setup alert queue for direct alerts
        await broker.declare_queue(
            "alerting.direct",
            "alerts.*",
            self.settings.rabbitmq.exchange_alerts
        )
        
        # Start consuming messages
        await broker.consume("alerting.analytics", self._process_analytics_message)
        await broker.consume("alerting.direct", self._process_direct_alert)
        
        # Start background tasks
        asyncio.create_task(self._alert_lifecycle_manager())
        
        logger.info("Alert Engine started successfully")
    
    async def stop(self):
        """Stop alert engine"""
        self.is_running = False
        logger.info("Alert Engine stopped")
    
    async def add_rule(self, rule: AlertRule):
        """Add alert rule"""
        self.rules[rule.id] = rule
        logger.info(f"Added alert rule: {rule.name}")
    
    async def remove_rule(self, rule_id: UUID):
        """Remove alert rule"""
        if rule_id in self.rules:
            del self.rules[rule_id]
            logger.info(f"Removed alert rule: {rule_id}")
    
    async def get_rules(self) -> List[AlertRule]:
        """Get all alert rules"""
        return list(self.rules.values())
    
    async def get_active_alerts(self) -> List[Alert]:
        """Get all active alerts"""
        return list(self.active_alerts.values())
    
    async def _process_analytics_message(self, envelope: MessageEnvelope):
        """Process analytics message for alert evaluation"""
        try:
            # Parse analytics data
            analytics_data = envelope.payload
            
            # Check if this matches any alert rules
            for rule in self.rules.values():
                if not rule.enabled:
                    continue
                
                # Evaluate rule condition
                if await self._evaluate_rule_condition(rule, analytics_data):
                    # Create alert context
                    context = AlertContext(
                        rule=rule,
                        event=None,  # Analytics data doesn't have source event
                        value=analytics_data.get("value", 0),
                        threshold=rule.threshold,
                        metadata=analytics_data
                    )
                    
                    # Fire alert
                    await self._fire_alert(context)
        
        except Exception as e:
            logger.error(f"Failed to process analytics message: {e}")
    
    async def _process_direct_alert(self, envelope: MessageEnvelope):
        """Process direct alert message"""
        try:
            # Parse alert data
            alert_data = envelope.payload
            
            # Create alert from data
            alert = Alert(
                rule_id=UUID(alert_data["rule_id"]),
                level=AlertLevel(alert_data["level"]),
                title=alert_data["title"],
                message=alert_data["message"],
                data=alert_data.get("data", {})
            )
            
            # Store active alert
            self.active_alerts[alert.id] = alert
            self.alert_states[alert.id] = AlertState.ACTIVE
            
            # Send notifications
            if alert.rule_id in self.rules:
                rule = self.rules[alert.rule_id]
                context = AlertContext(
                    rule=rule,
                    event=None,
                    value=alert_data.get("value", 0),
                    threshold=rule.threshold,
                    metadata=alert_data
                )
                
                await self._send_notifications(alert, context)
        
        except Exception as e:
            logger.error(f"Failed to process direct alert: {e}")
    
    async def _evaluate_rule_condition(self, rule: AlertRule, data: Dict[str, Any]) -> bool:
        """Evaluate rule condition against data"""
        try:
            # Simple condition evaluation (in production, use proper expression parser)
            condition = rule.condition
            
            # Replace placeholders with actual values
            for key, value in data.items():
                condition = condition.replace(f"${key}", str(value))
            
            # Evaluate condition
            return eval(condition, {"__builtins__": {}}, data)
        
        except Exception as e:
            logger.error(f"Failed to evaluate rule condition: {e}")
            return False
    
    async def _fire_alert(self, context: AlertContext):
        """Fire an alert"""
        try:
            # Check if alert is suppressed
            if await self._is_alert_suppressed(context.rule):
                logger.info(f"Alert suppressed for rule: {context.rule.name}")
                return
            
            # Create alert
            alert = Alert(
                rule_id=context.rule.id,
                level=context.rule.level,
                title=f"Alert: {context.rule.name}",
                message=f"Rule '{context.rule.name}' triggered. Value: {context.value}, Threshold: {context.threshold}",
                data=context.metadata
            )
            
            # Store alert
            self.active_alerts[alert.id] = alert
            self.alert_states[alert.id] = AlertState.ACTIVE
            
            # Send notifications
            await self._send_notifications(alert, context)
            
            logger.info(f"Alert fired: {alert.title}")
        
        except Exception as e:
            logger.error(f"Failed to fire alert: {e}")
    
    async def _send_notifications(self, alert: Alert, context: AlertContext):
        """Send notifications for alert"""
        try:
            # Get notification channels for rule
            channels = context.rule.channels
            
            # Send to each channel
            for channel in channels:
                if channel in self.notification_channels:
                    notification_channel = self.notification_channels[channel]
                    
                    # Check if channel is available
                    if await notification_channel.is_available():
                        success = await notification_channel.send(alert, context)
                        if success:
                            logger.info(f"Sent alert to {channel.value}")
                        else:
                            logger.error(f"Failed to send alert to {channel.value}")
                    else:
                        logger.warning(f"Channel {channel.value} is not available")
        
        except Exception as e:
            logger.error(f"Failed to send notifications: {e}")
    
    async def _is_alert_suppressed(self, rule: AlertRule) -> bool:
        """Check if alert is suppressed"""
        if rule.suppression_minutes <= 0:
            return False
        
        # Check if there's a recent alert for this rule
        cutoff_time = datetime.utcnow() - timedelta(minutes=rule.suppression_minutes)
        
        for alert in self.active_alerts.values():
            if (alert.rule_id == rule.id and 
                alert.timestamp > cutoff_time and
                not alert.resolved):
                return True
        
        return False
    
    async def _alert_lifecycle_manager(self):
        """Manage alert lifecycle (escalation, auto-resolution)"""
        while self.is_running:
            try:
                current_time = datetime.utcnow()
                
                # Check for escalations
                for alert_id, alert in list(self.active_alerts.items()):
                    if alert.resolved:
                        continue
                    
                    rule = self.rules.get(alert.rule_id)
                    if not rule:
                        continue
                    
                    # Check for escalation
                    if (rule.escalation_minutes > 0 and
                        not alert.acknowledged and
                        self.alert_states.get(alert_id) != AlertState.ESCALATED):
                        
                        escalation_time = alert.timestamp + timedelta(minutes=rule.escalation_minutes)
                        
                        if current_time >= escalation_time:
                            await self._escalate_alert(alert, rule)
                
                # Sleep before next check
                await asyncio.sleep(60)  # Check every minute
            
            except Exception as e:
                logger.error(f"Alert lifecycle manager error: {e}")
                await asyncio.sleep(60)
    
    async def _escalate_alert(self, alert: Alert, rule: AlertRule):
        """Escalate alert to higher level"""
        try:
            # Mark as escalated
            self.alert_states[alert.id] = AlertState.ESCALATED
            
            # Create escalation alert
            escalation_alert = Alert(
                rule_id=rule.id,
                level=AlertLevel.CRITICAL,
                title=f"ESCALATED: {alert.title}",
                message=f"Alert not acknowledged within {rule.escalation_minutes} minutes: {alert.message}",
                data=alert.data
            )
            
            # Send escalation notifications
            context = AlertContext(
                rule=rule,
                event=None,
                value=0,
                threshold=rule.threshold,
                metadata=alert.data
            )
            
            await self._send_notifications(escalation_alert, context)
            
            logger.warning(f"Alert escalated: {alert.title}")
        
        except Exception as e:
            logger.error(f"Failed to escalate alert: {e}")
    
    async def acknowledge_alert(self, alert_id: UUID, acknowledged_by: str):
        """Acknowledge alert"""
        if alert_id in self.active_alerts:
            alert = self.active_alerts[alert_id]
            alert.acknowledged = True
            alert.acknowledged_at = datetime.utcnow()
            alert.acknowledged_by = acknowledged_by
            
            logger.info(f"Alert acknowledged: {alert.title} by {acknowledged_by}")
    
    async def resolve_alert(self, alert_id: UUID, resolved_by: str):
        """Resolve alert"""
        if alert_id in self.active_alerts:
            alert = self.active_alerts[alert_id]
            alert.resolved = True
            alert.resolved_at = datetime.utcnow()
            alert.resolved_by = resolved_by
            
            # Remove from active alerts
            del self.active_alerts[alert_id]
            if alert_id in self.alert_states:
                del self.alert_states[alert_id]
            
            logger.info(f"Alert resolved: {alert.title} by {resolved_by}")
    
    async def get_health_status(self) -> HealthCheck:
        """Get health status"""
        try:
            # Check notification channels
            channel_health = {}
            for channel, notification_channel in self.notification_channels.items():
                channel_health[channel.value] = await notification_channel.is_available()
            
            # Check message broker
            broker = await get_message_broker()
            broker_health = broker.is_connected
            
            overall_status = HealthStatus.HEALTHY
            if not broker_health or not all(channel_health.values()):
                overall_status = HealthStatus.DEGRADED
            
            return HealthCheck(
                status=overall_status,
                service="alerting",
                version="0.1.0",
                checks={
                    "message_broker": broker_health,
                    "notification_channels": channel_health,
                    "active_alerts": len(self.active_alerts),
                    "rules_count": len(self.rules)
                }
            )
        
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return HealthCheck(
                status=HealthStatus.UNHEALTHY,
                service="alerting",
                version="0.1.0",
                checks={"error": str(e)}
            )


# Global service instance
alert_engine = AlertEngine()


async def authenticate_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Authenticate user"""
    if not credentials.credentials:
        raise HTTPException(status_code=401, detail="Invalid authentication credentials")
    return {"user_id": "authenticated_user"}


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events"""
    # Startup
    logger.info("Starting Alerting API Service...")
    
    # Initialize database
    db_manager = await get_database_manager()
    await db_manager.create_tables()
    
    # Start alert engine in background
    asyncio.create_task(alert_engine.start())
    
    logger.info("Alerting API Service started successfully")
    
    yield
    
    # Shutdown
    logger.info("Shutting down Alerting API Service...")
    await alert_engine.stop()
    await db_manager.close()
    logger.info("Alerting API Service stopped")


# Create FastAPI app
app = FastAPI(
    title="StreamFlow Alerting API",
    description="Real-time alerting and notification API",
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
            service="alerting",
            version="0.1.0",
            checks={
                "database": db_health,
                "message_broker": broker_health,
                "alert_engine": "running" if alert_engine.is_running else "stopped"
            }
        )
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return HealthCheck(
            status=HealthStatus.UNHEALTHY,
            service="alerting",
            version="0.1.0",
            checks={"error": str(e)}
        )


@app.get("/ready")
async def readiness_check():
    """Readiness check endpoint"""
    return {"status": "ready", "service": "alerting"}


# Alert endpoints
@app.get("/api/v1/alerts")
async def get_alerts(
    status: Optional[str] = Query(default=None),
    limit: int = Query(default=50, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
    user=Depends(authenticate_user)
):
    """Get alerts with optional status filtering"""
    
    try:
        db_manager = await get_database_manager()
        
        async with db_manager.get_session() as session:
            # Build query
            where_clause = ""
            params = {"limit": limit, "offset": offset}
            
            if status:
                where_clause = "WHERE status = :status"
                params["status"] = status
            
            query = text(f"""
                SELECT 
                    id, message, level, status, source, 
                    created_at, updated_at, data
                FROM alerts 
                {where_clause}
                ORDER BY created_at DESC
                LIMIT :limit OFFSET :offset
            """)
            
            result = await session.execute(query, params)
            
            alerts = []
            for row in result:
                alerts.append({
                    "id": str(row.id),
                    "message": row.message,
                    "level": row.level,
                    "status": row.status,
                    "source": row.source,
                    "created_at": row.created_at.isoformat() if row.created_at else None,
                    "updated_at": row.updated_at.isoformat() if row.updated_at else None,
                    "data": row.data
                })
        
        return APIResponse(
            success=True,
            message="Alerts retrieved successfully",
            data=alerts
        )
    except Exception as e:
        logger.error(f"Failed to get alerts: {e}")
        raise HTTPException(status_code=500, detail="Failed to get alerts")


@app.get("/api/v1/alerts/stats")
async def get_alert_stats(user=Depends(authenticate_user)):
    """Get alert statistics"""
    
    try:
        db_manager = await get_database_manager()
        
        async with db_manager.get_session() as session:
            # Check if alerts table exists and has data
            try:
                count_query = text("SELECT COUNT(*) as total FROM alerts")
                count_result = await session.execute(count_query)
                total_alerts = count_result.scalar()
                
                if total_alerts == 0:
                    # Return empty stats if no alerts exist
                    return APIResponse(
                        success=True,
                        message="Alert statistics retrieved successfully",
                        data={
                            "total": 0,
                            "by_status": {},
                            "by_level": {},
                            "recent_24h": 0
                        }
                    )
            except Exception:
                # Table might not exist yet, return empty stats
                return APIResponse(
                    success=True,
                    message="Alert statistics retrieved successfully (no alerts table)",
                    data={
                        "total": 0,
                        "by_status": {},
                        "by_level": {},
                        "recent_24h": 0
                    }
                )
            
            # Get alert counts by status
            status_query = text("""
                SELECT 
                    status,
                    COUNT(*) as count,
                    COUNT(CASE WHEN created_at >= NOW() - INTERVAL '24 hours' THEN 1 END) as recent_count
                FROM alerts 
                GROUP BY status
                ORDER BY status
            """)
            
            # Get alert counts by level
            level_query = text("""
                SELECT 
                    level,
                    COUNT(*) as count
                FROM alerts 
                GROUP BY level
                ORDER BY level
            """)
            
            status_result = await session.execute(status_query)
            level_result = await session.execute(level_query)
            
            stats = {
                "total": total_alerts,
                "by_status": {},
                "by_level": {},
                "recent_24h": 0
            }
            
            # Process status results
            for row in status_result:
                stats["by_status"][row.status] = row.count
                stats["recent_24h"] += row.recent_count
            
            # Process level results
            for row in level_result:
                stats["by_level"][row.level] = row.count
        
        return APIResponse(
            success=True,
            message="Alert statistics retrieved successfully",
            data=stats
        )
    except Exception as e:
        logger.error(f"Failed to get alert stats: {e}")
        raise HTTPException(status_code=500, detail="Failed to get alert stats")


@app.post("/api/v1/alerts/{alert_id}/acknowledge")
async def acknowledge_alert(
    alert_id: str,
    user=Depends(authenticate_user)
):
    """Acknowledge an alert"""
    
    try:
        db_manager = await get_database_manager()
        
        async with db_manager.get_session() as session:
            query = text("""
                UPDATE alerts 
                SET status = 'acknowledged', 
                    updated_at = NOW()
                WHERE id = :alert_id
                RETURNING id
            """)
            
            result = await session.execute(query, {"alert_id": alert_id})
            await session.commit()
            
            if not result.fetchone():
                raise HTTPException(status_code=404, detail="Alert not found")
        
        return APIResponse(
            success=True,
            message="Alert acknowledged successfully"
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to acknowledge alert: {e}")
        raise HTTPException(status_code=500, detail="Failed to acknowledge alert")


@app.post("/api/v1/alerts/{alert_id}/resolve")
async def resolve_alert(
    alert_id: str,
    user=Depends(authenticate_user)
):
    """Resolve an alert"""
    
    try:
        db_manager = await get_database_manager()
        
        async with db_manager.get_session() as session:
            query = text("""
                UPDATE alerts 
                SET status = 'resolved', 
                    updated_at = NOW()
                WHERE id = :alert_id
                RETURNING id
            """)
            
            result = await session.execute(query, {"alert_id": alert_id})
            await session.commit()
            
            if not result.fetchone():
                raise HTTPException(status_code=404, detail="Alert not found")
        
        return APIResponse(
            success=True,
            message="Alert resolved successfully"
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to resolve alert: {e}")
        raise HTTPException(status_code=500, detail="Failed to resolve alert")


async def main():
    """Main function to run alert engine"""
    try:
        await alert_engine.start()
        
        # Keep service running
        while alert_engine.is_running:
            await asyncio.sleep(1)
            
    except KeyboardInterrupt:
        logger.info("Received shutdown signal")
    except Exception as e:
        logger.error(f"Service error: {e}")
    finally:
        await alert_engine.stop()


if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=settings.services.alerting_port,
        log_level="info",
        reload=settings.debug
    )

