"""
Alert Engine Service - Rule-based alerting with multiple notification channels
StreamFlow - real-time analytics pipeline

 
"""
import asyncio
import logging
from abc import ABC, abstractmethod
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Union
from enum import Enum
from dataclasses import dataclass, field
from uuid import UUID, uuid4

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
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

# Global settings
settings = get_settings()

# Create FastAPI app
app = FastAPI(
    title="StreamFlow Alerting API",
    description="Real-time alerting and notification API",
    version="0.1.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Health check endpoint
@app.get("/health", response_model=HealthCheck)
async def health_check():
    """Health check endpoint"""
    try:
        # Check database
        db_manager = await get_database_manager()
        db_health = await db_manager.health_check()
        
        overall_status = HealthStatus.HEALTHY if db_health["status"] == "healthy" else HealthStatus.UNHEALTHY
        
        return HealthCheck(
            status=overall_status,
            service="alerting",
            version="0.1.0",
            checks={
                "database": db_health,
                "alert_engine": "healthy" if 'alert_engine' in globals() and alert_engine.is_running else "not_running"
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


@app.get("/api/v1/alerts")
async def get_alerts(
    status: Optional[str] = Query(default=None, description="Filter by alert status"),
    limit: int = Query(default=50, ge=1, le=1000, description="Maximum number of alerts to return"),
    hours: int = Query(default=24, ge=1, le=168, description="Number of hours to look back")
):
    """Get recent alerts from database"""
    try:
        db_manager = await get_database_manager()
        
        # Calculate time range
        start_time = datetime.utcnow() - timedelta(hours=hours)
        
        async with db_manager.get_session() as session:
            # Build query
            query = """
            SELECT 
                id, title, message, level, status, created_at, updated_at,
                rule_id, event_id, acknowledged_by, resolved_by
            FROM alerts 
            WHERE created_at >= :start_time
            """
            params = {"start_time": start_time}
            
            if status:
                query += " AND status = :status"
                params["status"] = status
            
            query += " ORDER BY created_at DESC LIMIT :limit"
            params["limit"] = limit
            
            result = await session.execute(text(query), params)
            rows = result.fetchall()
            
            # Convert to alert objects
            alerts = []
            for row in rows:
                alert_data = dict(row._mapping)
                alert_data['id'] = str(alert_data['id'])
                alerts.append(alert_data)
        
        return APIResponse(
            success=True,
            message=f"Retrieved {len(alerts)} alerts",
            data=alerts
        )
        
    except Exception as e:
        logger.error(f"Failed to get alerts: {e}")
        raise HTTPException(status_code=500, detail="Failed to get alerts")


@app.get("/api/v1/alerts/stats")
async def get_alert_stats():
    """Get alert statistics"""
    try:
        db_manager = await get_database_manager()
        
        async with db_manager.get_session() as session:
            # Get alert counts by status
            result = await session.execute(
                text("""
                SELECT 
                    status,
                    COUNT(*) as count
                FROM alerts 
                WHERE created_at >= :start_time
                GROUP BY status
                """),
                {"start_time": datetime.utcnow() - timedelta(hours=24)}
            )
            
            status_counts = dict(result.fetchall())
            
            # Get alert counts by level
            result = await session.execute(
                text("""
                SELECT 
                    level,
                    COUNT(*) as count
                FROM alerts 
                WHERE created_at >= :start_time
                GROUP BY level
                """),
                {"start_time": datetime.utcnow() - timedelta(hours=24)}
            )
            
            level_counts = dict(result.fetchall())
            
            # Get hourly alert trends
            result = await session.execute(
                text("""
                SELECT 
                    DATE_TRUNC('hour', created_at) as hour,
                    COUNT(*) as count
                FROM alerts 
                WHERE created_at >= :start_time
                GROUP BY DATE_TRUNC('hour', created_at)
                ORDER BY hour
                """),
                {"start_time": datetime.utcnow() - timedelta(hours=24)}
            )
            
            hourly_trends = [
                {
                    "hour": row[0].strftime("%H:%M"),
                    "count": row[1]
                }
                for row in result.fetchall()
            ]
        
        stats = {
            "status_counts": status_counts,
            "level_counts": level_counts,
            "hourly_trends": hourly_trends,
            "total_alerts_24h": sum(status_counts.values()),
            "active_alerts": status_counts.get("active", 0),
            "resolved_alerts": status_counts.get("resolved", 0)
        }
        
        return APIResponse(
            success=True,
            message="Alert statistics retrieved successfully",
            data=stats
        )
        
    except Exception as e:
        logger.error(f"Failed to get alert stats: {e}")
        raise HTTPException(status_code=500, detail="Failed to get alert stats")


@app.post("/api/v1/alerts/{alert_id}/acknowledge")
async def acknowledge_alert(alert_id: str):
    """Acknowledge an alert"""
    try:
        db_manager = await get_database_manager()
        
        async with db_manager.get_session() as session:
            result = await session.execute(
                text("""
                UPDATE alerts 
                SET status = 'acknowledged', 
                    updated_at = :now,
                    acknowledged_by = 'api_user'
                WHERE id = :alert_id
                """),
                {"alert_id": alert_id, "now": datetime.utcnow()}
            )
            
            if result.rowcount == 0:
                raise HTTPException(status_code=404, detail="Alert not found")
            
            await session.commit()
        
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
async def resolve_alert(alert_id: str):
    """Resolve an alert"""
    try:
        db_manager = await get_database_manager()
        
        async with db_manager.get_session() as session:
            result = await session.execute(
                text("""
                UPDATE alerts 
                SET status = 'resolved', 
                    updated_at = :now,
                    resolved_by = 'api_user'
                WHERE id = :alert_id
                """),
                {"alert_id": alert_id, "now": datetime.utcnow()}
            )
            
            if result.rowcount == 0:
                raise HTTPException(status_code=404, detail="Alert not found")
            
            await session.commit()
        
        return APIResponse(
            success=True,
            message="Alert resolved successfully"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to resolve alert: {e}")
        raise HTTPException(status_code=500, detail="Failed to resolve alert")


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


async def start_alert_engine():
    """Start the alert engine"""
    await alert_engine.start()


async def main():
    """Main function to run alert engine"""
    try:
        # Start alert engine in background
        engine_task = asyncio.create_task(start_alert_engine())
        
        # Start FastAPI server
        config = uvicorn.Config(
            app, 
            host="0.0.0.0", 
            port=settings.services.alerting_port,
            log_level="info"
        )
        server = uvicorn.Server(config)
        
        # Run both services concurrently
        await asyncio.gather(
            server.serve(),
            engine_task
        )
            
    except KeyboardInterrupt:
        logger.info("Received shutdown signal")
    except Exception as e:
        logger.error(f"Service error: {e}")
    finally:
        await alert_engine.stop()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(main())
