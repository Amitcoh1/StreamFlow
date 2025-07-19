"""
Analytics Pipeline Service - Stream processing and analytics engine
StreamFlow - real-time analytics pipeline

 
"""
import asyncio
import logging
from collections import defaultdict, deque
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Callable, Any
from uuid import UUID
import json

from streamflow.shared.config import get_settings
from streamflow.shared.models import Event, EventType, MetricData, MetricType, ProcessingResult, ProcessingStatus
from streamflow.shared.messaging import get_message_broker, get_event_publisher, MessageEnvelope
from streamflow.shared.database import get_database_manager

logger = logging.getLogger(__name__)

# Global state
settings = get_settings()


class TimeWindow:
    """Time-based window for stream processing"""
    
    def __init__(self, size_seconds: int, slide_seconds: int = None):
        self.size_seconds = size_seconds
        self.slide_seconds = slide_seconds or size_seconds
        self.data = deque()
    
    def add_event(self, event: Event):
        """Add event to window"""
        self.data.append(event)
        self._cleanup_old_events()
    
    def _cleanup_old_events(self):
        """Remove events older than window size"""
        cutoff_time = datetime.utcnow() - timedelta(seconds=self.size_seconds)
        while self.data and self.data[0].timestamp < cutoff_time:
            self.data.popleft()
    
    def get_events(self) -> List[Event]:
        """Get all events in current window"""
        self._cleanup_old_events()
        return list(self.data)
    
    def count(self) -> int:
        """Count events in current window"""
        self._cleanup_old_events()
        return len(self.data)


class StreamProcessor:
    """Stream processing engine with windowing and aggregations"""
    
    def __init__(self):
        self.windows: Dict[str, TimeWindow] = {}
        self.aggregators: Dict[str, Callable] = {}
        self.rules: List[Dict[str, Any]] = []
        self.metrics: Dict[str, Any] = defaultdict(int)
        
    def register_window(self, name: str, size_seconds: int, slide_seconds: int = None):
        """Register a time window"""
        self.windows[name] = TimeWindow(size_seconds, slide_seconds)
        logger.info(f"Registered window: {name} (size: {size_seconds}s)")
    
    def register_aggregator(self, name: str, func: Callable):
        """Register an aggregation function"""
        self.aggregators[name] = func
        logger.info(f"Registered aggregator: {name}")
    
    def register_rule(self, name: str, condition: str, action: Callable):
        """Register a processing rule"""
        self.rules.append({
            "name": name,
            "condition": condition,
            "action": action
        })
        logger.info(f"Registered rule: {name}")
    
    async def process_event(self, event: Event) -> List[ProcessingResult]:
        """Process incoming event through all windows and rules"""
        results = []
        
        try:
            # Add event to all windows
            for window_name, window in self.windows.items():
                window.add_event(event)
            
            # Update metrics
            self.metrics["events_processed"] += 1
            self.metrics[f"events_by_type_{event.type.value}"] += 1
            
            # Apply rules
            for rule in self.rules:
                try:
                    if await self._evaluate_condition(rule["condition"], event):
                        result = await rule["action"](event)
                        if result:
                            results.append(ProcessingResult(
                                event_id=event.id,
                                status=ProcessingStatus.COMPLETED,
                                output=result
                            ))
                except Exception as e:
                    logger.error(f"Rule {rule['name']} failed: {e}")
                    results.append(ProcessingResult(
                        event_id=event.id,
                        status=ProcessingStatus.FAILED,
                        error=str(e)
                    ))
            
            # Generate metrics
            await self._generate_metrics(event)
            
        except Exception as e:
            logger.error(f"Event processing failed: {e}")
            results.append(ProcessingResult(
                event_id=event.id,
                status=ProcessingStatus.FAILED,
                error=str(e)
            ))
        
        return results
    
    async def _evaluate_condition(self, condition: str, event: Event) -> bool:
        """Evaluate rule condition"""
        # Simple condition evaluation (in production, use a proper expression parser)
        try:
            # Create evaluation context
            context = {
                "event": event,
                "event_type": event.type.value,
                "severity": event.severity.value,
                "source": event.source,
                "data": event.data,
                "tags": event.tags,
                "windows": self.windows,
                "metrics": self.metrics
            }
            
            # Evaluate condition
            return eval(condition, {"__builtins__": {}}, context)
        except Exception as e:
            logger.error(f"Condition evaluation failed: {e}")
            return False
    
    async def _generate_metrics(self, event: Event):
        """Generate metrics from event"""
        try:
            # Event count metrics
            await self._emit_metric(
                "events_total",
                MetricType.COUNTER,
                1,
                {"source": event.source, "type": event.type.value}
            )
            
            # Event severity metrics
            await self._emit_metric(
                "events_by_severity",
                MetricType.COUNTER,
                1,
                {"severity": event.severity.value}
            )
            
            # Processing time metrics
            processing_time = (datetime.utcnow() - event.timestamp).total_seconds()
            await self._emit_metric(
                "event_processing_time",
                MetricType.HISTOGRAM,
                processing_time,
                {"source": event.source}
            )
            
            # Window-based metrics
            for window_name, window in self.windows.items():
                await self._emit_metric(
                    f"window_{window_name}_count",
                    MetricType.GAUGE,
                    window.count(),
                    {"window": window_name}
                )
        
        except Exception as e:
            logger.error(f"Metric generation failed: {e}")
    
    async def _emit_metric(self, name: str, metric_type: MetricType, value: float, tags: Dict[str, str]):
        """Emit metric to analytics exchange"""
        try:
            metric = MetricData(
                name=name,
                type=metric_type,
                value=value,
                tags=tags
            )
            
            publisher = await get_event_publisher()
            await publisher.publish_metric(metric.dict())
            
        except Exception as e:
            logger.error(f"Metric emission failed: {e}")


class AnalyticsService:
    """Main analytics service"""
    
    def __init__(self):
        self.processor = StreamProcessor()
        self.is_running = False
        self._setup_default_processing()
    
    def _setup_default_processing(self):
        """Setup default processing windows and rules"""
        # Register time windows
        self.processor.register_window("1min", 60)
        self.processor.register_window("5min", 300)
        self.processor.register_window("1hour", 3600)
        
        # Register aggregators
        self.processor.register_aggregator("count", lambda events: len(events))
        self.processor.register_aggregator("avg", lambda events: sum(e.data.get("value", 0) for e in events) / len(events) if events else 0)
        
        # Register rules
        self.processor.register_rule(
            "high_error_rate",
            "event_type == 'error' and windows['1min'].count() > 10",
            self._handle_high_error_rate
        )
        
        self.processor.register_rule(
            "user_activity_spike",
            "event_type in ['user.login', 'user.logout'] and windows['5min'].count() > 100",
            self._handle_activity_spike
        )
    
    async def _handle_high_error_rate(self, event: Event) -> Dict[str, Any]:
        """Handle high error rate condition"""
        error_count = self.processor.windows["1min"].count()
        
        alert_data = {
            "alert_type": "high_error_rate",
            "message": f"High error rate detected: {error_count} errors in 1 minute",
            "severity": "critical",
            "event_id": str(event.id),
            "timestamp": datetime.utcnow().isoformat()
        }
        
        # Publish alert
        publisher = await get_event_publisher()
        await publisher.publish_alert(alert_data)
        
        return alert_data
    
    async def _handle_activity_spike(self, event: Event) -> Dict[str, Any]:
        """Handle user activity spike"""
        activity_count = self.processor.windows["5min"].count()
        
        alert_data = {
            "alert_type": "activity_spike",
            "message": f"User activity spike detected: {activity_count} events in 5 minutes",
            "severity": "warning",
            "event_id": str(event.id),
            "timestamp": datetime.utcnow().isoformat()
        }
        
        # Publish alert
        publisher = await get_event_publisher()
        await publisher.publish_alert(alert_data)
        
        return alert_data
    
    async def start(self):
        """Start analytics service"""
        if self.is_running:
            return
        
        self.is_running = True
        logger.info("Starting Analytics Service...")
        
        # Initialize message broker
        broker = await get_message_broker()
        
        # Setup event queue
        await broker.declare_queue(
            "analytics.events",
            "events.*",
            settings.rabbitmq.exchange_events
        )
        
        # Start consuming events
        await broker.consume(
            "analytics.events",
            self._process_message,
            auto_ack=False
        )
        
        logger.info("Analytics Service started successfully")
    
    async def stop(self):
        """Stop analytics service"""
        self.is_running = False
        logger.info("Analytics Service stopped")
    
    async def _process_message(self, envelope: MessageEnvelope):
        """Process incoming message"""
        try:
            # Parse event from message
            event_data = envelope.payload
            event = Event(**event_data)
            
            # Process event
            results = await self.processor.process_event(event)
            
            # Log processing results
            for result in results:
                if result.status == ProcessingStatus.COMPLETED:
                    logger.info(f"Event {event.id} processed successfully")
                else:
                    logger.error(f"Event {event.id} processing failed: {result.error}")
        
        except Exception as e:
            logger.error(f"Message processing failed: {e}")
    
    async def get_metrics(self) -> Dict[str, Any]:
        """Get service metrics"""
        return {
            "service": "analytics",
            "metrics": dict(self.processor.metrics),
            "windows": {
                name: window.count() 
                for name, window in self.processor.windows.items()
            },
            "rules_count": len(self.processor.rules),
            "timestamp": datetime.utcnow().isoformat()
        }
    
    async def get_window_data(self, window_name: str) -> List[Dict[str, Any]]:
        """Get data from specific window"""
        if window_name not in self.processor.windows:
            raise ValueError(f"Window {window_name} not found")
        
        window = self.processor.windows[window_name]
        events = window.get_events()
        
        return [
            {
                "id": str(event.id),
                "type": event.type.value,
                "source": event.source,
                "timestamp": event.timestamp.isoformat(),
                "data": event.data
            }
            for event in events
        ]


# Global service instance
analytics_service = AnalyticsService()


async def main():
    """Main function to run analytics service"""
    try:
        await analytics_service.start()
        
        # Keep service running
        while analytics_service.is_running:
            await asyncio.sleep(1)
            
    except KeyboardInterrupt:
        logger.info("Received shutdown signal")
    except Exception as e:
        logger.error(f"Service error: {e}")
    finally:
        await analytics_service.stop()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(main())
