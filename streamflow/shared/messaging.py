"""
RabbitMQ messaging utilities with async support
StreamFlow - real-time analytics pipeline

 
"""
import asyncio
import json
import logging
from contextlib import asynccontextmanager
from typing import Any, Callable, Dict, List, Optional, Union
from uuid import uuid4
from datetime import datetime

import aio_pika
from aio_pika import Connection, Channel, Exchange, Queue, Message
from aio_pika.abc import AbstractRobustConnection
from aio_pika.patterns import RPC

from .config import Settings, get_settings
from .models import MessageEnvelope, Event

logger = logging.getLogger(__name__)


class MessageBroker:
    """RabbitMQ message broker with connection pooling and resilience"""
    
    def __init__(self, settings: Optional[Settings] = None):
        self.settings = settings or get_settings()
        self.connection: Optional[AbstractRobustConnection] = None
        self.channel: Optional[Channel] = None
        self.exchanges: Dict[str, Exchange] = {}
        self.queues: Dict[str, Queue] = {}
        self.is_connected = False
        
    async def connect(self):
        """Establish connection to RabbitMQ"""
        try:
            self.connection = await aio_pika.connect_robust(
                self.settings.rabbitmq.url,
                heartbeat=self.settings.rabbitmq.heartbeat,
                loop=asyncio.get_event_loop()
            )
            self.channel = await self.connection.channel()
            await self.channel.set_qos(prefetch_count=10)
            
            # Declare exchanges
            await self._declare_exchanges()
            
            self.is_connected = True
            logger.info("Connected to RabbitMQ")
            
        except Exception as e:
            logger.error(f"Failed to connect to RabbitMQ: {e}")
            raise
    
    async def disconnect(self):
        """Close connection to RabbitMQ"""
        if self.connection:
            await self.connection.close()
            self.is_connected = False
            logger.info("Disconnected from RabbitMQ")
    
    async def _declare_exchanges(self):
        """Declare required exchanges"""
        exchange_configs = [
            (self.settings.rabbitmq.exchange_events, "topic"),
            (self.settings.rabbitmq.exchange_analytics, "topic"),
            (self.settings.rabbitmq.exchange_alerts, "topic"),
        ]
        
        for exchange_name, exchange_type in exchange_configs:
            exchange = await self.channel.declare_exchange(
                exchange_name,
                type=exchange_type,
                durable=True
            )
            self.exchanges[exchange_name] = exchange
            logger.info(f"Declared exchange: {exchange_name} ({exchange_type})")
    
    async def declare_queue(
        self,
        queue_name: str,
        routing_key: str,
        exchange_name: str,
        durable: bool = True,
        arguments: Optional[Dict[str, Any]] = None
    ) -> Queue:
        """Declare a queue and bind it to an exchange"""
        if not self.is_connected:
            await self.connect()
        
        queue = await self.channel.declare_queue(
            queue_name,
            durable=durable,
            arguments=arguments or {}
        )
        
        if exchange_name in self.exchanges:
            await queue.bind(self.exchanges[exchange_name], routing_key)
            logger.info(f"Bound queue {queue_name} to exchange {exchange_name} with routing key {routing_key}")
        
        self.queues[queue_name] = queue
        return queue
    
    async def publish(
        self,
        exchange_name: str,
        routing_key: str,
        message: Union[Dict[str, Any], MessageEnvelope],
        correlation_id: Optional[str] = None,
        priority: int = 0,
        expiration: Optional[int] = None
    ):
        """Publish message to exchange"""
        if not self.is_connected:
            await self.connect()
        
        # Convert to MessageEnvelope if needed
        if isinstance(message, dict):
            envelope = MessageEnvelope(
                routing_key=routing_key,
                payload=message,
                correlation_id=correlation_id or str(uuid4()),
                priority=priority,
                expiration=expiration
            )
        else:
            envelope = message
        
        # Serialize message
        message_body = json.dumps(envelope.dict(), default=str)
        
        # Create aio_pika message
        aio_message = Message(
            message_body.encode(),
            correlation_id=envelope.correlation_id,
            priority=envelope.priority,
            expiration=envelope.expiration,
            timestamp=datetime.utcnow(),
            headers=envelope.headers
        )
        
        # Publish message
        exchange = self.exchanges.get(exchange_name)
        if not exchange:
            raise ValueError(f"Exchange {exchange_name} not found")
        
        await exchange.publish(aio_message, routing_key=routing_key)
        logger.debug(f"Published message to {exchange_name}.{routing_key}")
    
    async def consume(
        self,
        queue_name: str,
        callback: Callable,
        auto_ack: bool = False,
        exclusive: bool = False
    ):
        """Consume messages from queue"""
        if not self.is_connected:
            await self.connect()
        
        queue = self.queues.get(queue_name)
        if not queue:
            raise ValueError(f"Queue {queue_name} not found")
        
        async def message_handler(message: Message):
            """Handle incoming message"""
            try:
                # Deserialize message
                envelope = MessageEnvelope.parse_raw(message.body)
                
                # Process message
                await callback(envelope)
                
                # Acknowledge message if not auto-ack
                if not auto_ack:
                    await message.ack()
                
            except Exception as e:
                logger.error(f"Error processing message: {e}")
                if not auto_ack:
                    await message.reject()
        
        # Start consuming
        await queue.consume(message_handler, exclusive=exclusive)
        logger.info(f"Started consuming from queue: {queue_name}")
    
    async def rpc_call(
        self,
        exchange_name: str,
        routing_key: str,
        message: Dict[str, Any],
        timeout: int = 30
    ) -> Any:
        """Make RPC call"""
        if not self.is_connected:
            await self.connect()
        
        rpc = RPC(self.channel)
        
        try:
            response = await rpc.call(
                exchange_name,
                routing_key,
                json.dumps(message, default=str),
                timeout=timeout
            )
            return json.loads(response.decode())
        except Exception as e:
            logger.error(f"RPC call failed: {e}")
            raise
    
    async def setup_dead_letter_queue(
        self,
        queue_name: str,
        exchange_name: str,
        routing_key: str,
        ttl: int = 300000  # 5 minutes
    ) -> Queue:
        """Setup dead letter queue for failed messages"""
        dlq_name = f"{queue_name}.dlq"
        dlx_name = f"{exchange_name}.dlx"
        
        # Declare dead letter exchange
        dlx = await self.channel.declare_exchange(
            dlx_name,
            type="direct",
            durable=True
        )
        
        # Declare dead letter queue
        dlq = await self.channel.declare_queue(
            dlq_name,
            durable=True
        )
        
        # Bind dead letter queue to dead letter exchange
        await dlq.bind(dlx, routing_key)
        
        # Declare main queue with dead letter configuration
        main_queue = await self.channel.declare_queue(
            queue_name,
            durable=True,
            arguments={
                "x-dead-letter-exchange": dlx_name,
                "x-dead-letter-routing-key": routing_key,
                "x-message-ttl": ttl
            }
        )
        
        # Bind main queue to main exchange
        if exchange_name in self.exchanges:
            await main_queue.bind(self.exchanges[exchange_name], routing_key)
        
        self.queues[queue_name] = main_queue
        self.queues[dlq_name] = dlq
        
        logger.info(f"Setup dead letter queue: {dlq_name}")
        return main_queue
    
    @asynccontextmanager
    async def transaction(self):
        """Context manager for transactional operations"""
        if not self.is_connected:
            await self.connect()
        
        tx = self.channel.transaction()
        await tx.select()
        
        try:
            yield tx
            await tx.commit()
        except Exception:
            await tx.rollback()
            raise
    
    async def get_queue_info(self, queue_name: str) -> Dict[str, Any]:
        """Get queue information"""
        if not self.is_connected:
            await self.connect()
        
        queue = self.queues.get(queue_name)
        if not queue:
            raise ValueError(f"Queue {queue_name} not found")
        
        # This is a simplified version - in production you'd use management API
        return {
            "name": queue_name,
            "durable": queue.durable,
            "exclusive": queue.exclusive,
            "auto_delete": queue.auto_delete,
            "arguments": queue.arguments
        }
    
    async def purge_queue(self, queue_name: str):
        """Purge all messages from queue"""
        if not self.is_connected:
            await self.connect()
        
        queue = self.queues.get(queue_name)
        if not queue:
            raise ValueError(f"Queue {queue_name} not found")
        
        await queue.purge()
        logger.info(f"Purged queue: {queue_name}")


class EventPublisher:
    """High-level event publisher"""
    
    def __init__(self, broker: MessageBroker):
        self.broker = broker
    
    async def publish_event(
        self,
        event: Event,
        routing_key: Optional[str] = None
    ):
        """Publish event to events exchange"""
        routing_key = routing_key or f"events.{event.type.value}"
        
        await self.broker.publish(
            exchange_name=self.broker.settings.rabbitmq.exchange_events,
            routing_key=routing_key,
            message=event.dict(),
            correlation_id=event.correlation_id
        )
    
    async def publish_metric(
        self,
        metric_data: Dict[str, Any],
        routing_key: Optional[str] = None
    ):
        """Publish metric to analytics exchange"""
        routing_key = routing_key or "analytics.metrics"
        
        await self.broker.publish(
            exchange_name=self.broker.settings.rabbitmq.exchange_analytics,
            routing_key=routing_key,
            message=metric_data
        )
    
    async def publish_alert(
        self,
        alert_data: Dict[str, Any],
        routing_key: Optional[str] = None
    ):
        """Publish alert to alerts exchange"""
        routing_key = routing_key or "alerts.notification"
        
        await self.broker.publish(
            exchange_name=self.broker.settings.rabbitmq.exchange_alerts,
            routing_key=routing_key,
            message=alert_data
        )


# Global instances
_broker: Optional[MessageBroker] = None
_publisher: Optional[EventPublisher] = None


async def get_message_broker() -> MessageBroker:
    """Get global message broker instance"""
    global _broker
    if _broker is None:
        _broker = MessageBroker()
        await _broker.connect()
    return _broker


async def get_event_publisher() -> EventPublisher:
    """Get global event publisher instance"""
    global _publisher
    if _publisher is None:
        broker = await get_message_broker()
        _publisher = EventPublisher(broker)
    return _publisher


async def cleanup_messaging():
    """Cleanup global messaging resources"""
    global _broker, _publisher
    if _broker:
        await _broker.disconnect()
        _broker = None
    _publisher = None
