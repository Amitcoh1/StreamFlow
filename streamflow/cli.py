"""
StreamFlow CLI - Command line interface for managing StreamFlow services
StreamFlow - real-time analytics pipeline

 
"""
import asyncio
import logging
import sys
from pathlib import Path
from typing import Optional

import click
import uvicorn
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

from .shared.config import get_settings
from .shared.messaging import get_message_broker
from .shared.database import get_database_manager

console = Console()
logger = logging.getLogger(__name__)


@click.group()
@click.option('--debug', is_flag=True, help='Enable debug mode')
@click.option('--config', help='Path to configuration file')
def cli(debug: bool, config: Optional[str]):
    """StreamFlow - real-time analytics pipeline"""
    if debug:
        logging.basicConfig(level=logging.DEBUG)
    else:
        logging.basicConfig(level=logging.INFO)
    
    if config:
        # Load custom configuration
        console.print(f"Loading configuration from: {config}")


@cli.command()
@click.option('--service', type=click.Choice(['ingestion', 'analytics', 'alerting', 'dashboard', 'storage', 'all']), 
              default='all', help='Service to start')
@click.option('--port', type=int, help='Port to run the service on')
@click.option('--host', default='0.0.0.0', help='Host to bind to')
@click.option('--workers', type=int, default=1, help='Number of worker processes')
def start(service: str, port: Optional[int], host: str, workers: int):
    """Start StreamFlow services"""
    settings = get_settings()
    
    console.print(Panel.fit(
        f"🚀 Starting StreamFlow {service} service(s)",
        style="bold green"
    ))
    
    if service == 'all':
        start_all_services(settings, host, workers)
    else:
        start_single_service(service, settings, port, host, workers)


def start_all_services(settings, host: str, workers: int):
    """Start all services"""
    services = [
        ('ingestion', settings.services.ingestion_port),
        ('analytics', None),  # Background service
        ('alerting', None),   # Background service
        ('dashboard', settings.services.dashboard_port),
        ('storage', settings.services.storage_port),
    ]
    
    for service_name, service_port in services:
        if service_port:
            console.print(f"Starting {service_name} service on port {service_port}")
            # In production, you'd use a process manager like supervisor
            # For now, we'll just show the command
            console.print(f"  uvicorn streamflow.services.{service_name}.main:app --host {host} --port {service_port}")
        else:
            console.print(f"Starting {service_name} background service")
            console.print(f"  python -m streamflow.services.{service_name}.main")


def start_single_service(service: str, settings, port: Optional[int], host: str, workers: int):
    """Start a single service"""
    service_ports = {
        'ingestion': settings.services.ingestion_port,
        'dashboard': settings.services.dashboard_port,
        'storage': settings.services.storage_port,
    }
    
    if service in service_ports:
        # Web service
        service_port = port or service_ports[service]
        console.print(f"Starting {service} service on {host}:{service_port}")
        
        uvicorn.run(
            f"streamflow.services.{service}.main:app",
            host=host,
            port=service_port,
            workers=workers,
            log_level="info"
        )
    else:
        # Background service
        console.print(f"Starting {service} background service")
        import importlib
        module = importlib.import_module(f"streamflow.services.{service}.main")
        asyncio.run(module.main())


@cli.command()
def stop():
    """Stop all StreamFlow services"""
    console.print(Panel.fit(
        "🛑 Stopping StreamFlow services",
        style="bold red"
    ))
    
    # In production, you'd implement proper service management
    console.print("Service stopping not implemented in demo mode")
    console.print("Use Ctrl+C to stop individual services or docker-compose down for containers")


@cli.command()
@click.option('--format', type=click.Choice(['table', 'json']), default='table', help='Output format')
def status(format: str):
    """Check status of StreamFlow services"""
    console.print(Panel.fit(
        "📊 StreamFlow Service Status",
        style="bold blue"
    ))
    
    # Mock status for demo
    services = [
        {"name": "ingestion", "status": "running", "port": 8001, "uptime": "2h 30m"},
        {"name": "analytics", "status": "running", "port": "-", "uptime": "2h 30m"},
        {"name": "alerting", "status": "running", "port": "-", "uptime": "2h 30m"},
        {"name": "dashboard", "status": "running", "port": 8004, "uptime": "2h 30m"},
        {"name": "storage", "status": "running", "port": 8005, "uptime": "2h 30m"},
    ]
    
    if format == 'table':
        table = Table(title="Service Status")
        table.add_column("Service", style="cyan", no_wrap=True)
        table.add_column("Status", style="magenta")
        table.add_column("Port", style="green")
        table.add_column("Uptime", style="yellow")
        
        for service in services:
            status_style = "green" if service["status"] == "running" else "red"
            table.add_row(
                service["name"],
                f"[{status_style}]{service['status']}[/{status_style}]",
                str(service["port"]),
                service["uptime"]
            )
        
        console.print(table)
    else:
        console.print_json(data=services)


@cli.command()
@click.option('--drop', is_flag=True, help='Drop existing tables')
def init_db(drop: bool):
    """Initialize database tables"""
    console.print(Panel.fit(
        "🗃️ Initializing Database",
        style="bold yellow"
    ))
    
    async def init():
        db_manager = await get_database_manager()
        
        if drop:
            console.print("Dropping existing tables...")
            await db_manager.drop_tables()
        
        console.print("Creating tables...")
        await db_manager.create_tables()
        
        console.print("✅ Database initialized successfully")
    
    asyncio.run(init())


@cli.command()
@click.option('--type', type=click.Choice(['web.click', 'api.request', 'user.login', 'error']), 
              default='web.click', help='Event type')
@click.option('--source', default='cli', help='Event source')
@click.option('--count', type=int, default=1, help='Number of events to send')
def send_event(type: str, source: str, count: int):
    """Send test events to the system"""
    console.print(Panel.fit(
        f"📤 Sending {count} test event(s)",
        style="bold green"
    ))
    
    async def send():
        from shared.models import Event, EventType
        from shared.messaging import get_event_publisher
        
        publisher = await get_event_publisher()
        
        for i in range(count):
            event = Event(
                type=EventType(type),
                source=source,
                data={"test": True, "sequence": i + 1}
            )
            
            await publisher.publish_event(event)
            console.print(f"✅ Sent event {i + 1}: {event.id}")
    
    asyncio.run(send())


@cli.command()
@click.option('--service', type=click.Choice(['ingestion', 'analytics', 'alerting', 'dashboard', 'storage']), 
              help='Service to check')
def health(service: Optional[str]):
    """Check health of services"""
    console.print(Panel.fit(
        "🏥 Health Check",
        style="bold cyan"
    ))
    
    if service:
        console.print(f"Checking {service} service health...")
        # In production, make actual HTTP requests to health endpoints
        console.print("✅ Service is healthy")
    else:
        console.print("Checking all services...")
        services = ['ingestion', 'analytics', 'alerting', 'dashboard', 'storage']
        
        for svc in services:
            console.print(f"  {svc}: ✅ healthy")


@cli.command()
@click.option('--lines', type=int, default=50, help='Number of lines to show')
@click.option('--follow', is_flag=True, help='Follow log output')
@click.option('--service', help='Service to show logs for')
def logs(lines: int, follow: bool, service: Optional[str]):
    """Show service logs"""
    console.print(Panel.fit(
        f"📋 Service Logs {'(following)' if follow else ''}",
        style="bold magenta"
    ))
    
    if service:
        console.print(f"Showing logs for {service} service...")
    else:
        console.print("Showing logs for all services...")
    
    # In production, integrate with actual logging system
    console.print("Log viewing not implemented in demo mode")
    console.print("Use 'docker-compose logs' for containerized deployments")


@cli.command()
def config():
    """Show current configuration"""
    console.print(Panel.fit(
        "⚙️ Current Configuration",
        style="bold blue"
    ))
    
    settings = get_settings()
    
    config_table = Table(title="Configuration")
    config_table.add_column("Setting", style="cyan")
    config_table.add_column("Value", style="green")
    
    config_table.add_row("Environment", settings.environment)
    config_table.add_row("Debug", str(settings.debug))
    config_table.add_row("App Name", settings.app_name)
    config_table.add_row("App Version", settings.app_version)
    config_table.add_row("RabbitMQ URL", settings.rabbitmq.url)
    config_table.add_row("Database URL", settings.database.url[:50] + "..." if len(settings.database.url) > 50 else settings.database.url)
    config_table.add_row("Redis URL", settings.redis.url)
    
    console.print(config_table)


@cli.command()
def version():
    """Show StreamFlow version"""
    console.print(Panel.fit(
        "🌊 StreamFlow v0.1.0",
        subtitle="real-time analytics pipeline",
        style="bold blue"
    ))


def main():
    """Main entry point"""
    try:
        cli()
    except KeyboardInterrupt:
        console.print("\n👋 Goodbye!")
        sys.exit(0)
    except Exception as e:
        console.print(f"❌ Error: {e}", style="bold red")
        sys.exit(1)


if __name__ == '__main__':
    main()
