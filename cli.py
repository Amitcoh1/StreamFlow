#!/usr/bin/env python3
"""
StreamFlow CLI - Command Line Interface for StreamFlow Analytics Platform
"""
import asyncio
import os
import sys
import subprocess
import json
from pathlib import Path
from typing import Optional, List

import click
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.table import Table
from rich.text import Text

console = Console()


class StreamFlowCLI:
    """StreamFlow command line interface"""
    
    def __init__(self):
        self.base_dir = Path.cwd()
        self.config_dir = self.base_dir / ".streamflow"
        self.docker_compose_file = self.base_dir / "docker-compose.yml"
    
    def create_project_structure(self, project_name: str) -> None:
        """Create a new StreamFlow project structure"""
        project_path = self.base_dir / project_name
        project_path.mkdir(exist_ok=True)
        
        # Create project directories
        directories = [
            "config",
            "logs",
            "data",
            "dashboards",
            "alerts",
            "scripts",
            "docs"
        ]
        
        for directory in directories:
            (project_path / directory).mkdir(exist_ok=True)
        
        # Create configuration files
        self._create_config_files(project_path)
        self._create_docker_compose(project_path)
        self._create_env_file(project_path)
        self._create_readme(project_path, project_name)
    
    def _create_config_files(self, project_path: Path) -> None:
        """Create configuration files"""
        config_path = project_path / "config"
        
        # Main configuration
        config = {
            "project": {
                "name": project_path.name,
                "version": "0.1.0",
                "description": "StreamFlow Analytics Project"
            },
            "services": {
                "ingestion_port": 8001,
                "analytics_port": 8002,
                "alerting_port": 8003,
                "storage_port": 8004,
                "dashboard_port": 8005
            },
            "database": {
                "host": "localhost",
                "port": 5432,
                "name": "streamflow",
                "user": "streamflow"
            },
            "redis": {
                "host": "localhost",
                "port": 6379
            },
            "rabbitmq": {
                "host": "localhost",
                "port": 5672,
                "user": "admin"
            }
        }
        
        with open(config_path / "config.json", "w") as f:
            json.dump(config, f, indent=2)
    
    def _create_docker_compose(self, project_path: Path) -> None:
        """Create docker-compose.yml file"""
        compose_content = """version: '3.8'

services:
  # Infrastructure Services
  postgres:
    image: postgres:15
    environment:
      POSTGRES_DB: streamflow
      POSTGRES_USER: streamflow
      POSTGRES_PASSWORD: streamflow123
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data
    networks:
      - streamflow-network

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data
    networks:
      - streamflow-network

  rabbitmq:
    image: rabbitmq:3-management
    environment:
      RABBITMQ_DEFAULT_USER: admin
      RABBITMQ_DEFAULT_PASS: admin123
    ports:
      - "5672:5672"
      - "15672:15672"
    volumes:
      - rabbitmq_data:/var/lib/rabbitmq
    networks:
      - streamflow-network

  # StreamFlow Services
  streamflow-all:
    image: streamflow/streamflow:latest
    ports:
      - "8001:8001"  # Ingestion
      - "8002:8002"  # Analytics
      - "8003:8003"  # Alerting
      - "8004:8004"  # Storage
      - "8005:8005"  # Dashboard
      - "3001:3001"  # React UI
    environment:
      - DATABASE_URL=postgresql+asyncpg://streamflow:streamflow123@postgres:5432/streamflow
      - REDIS_URL=redis://redis:6379
      - RABBITMQ_URL=amqp://admin:admin123@rabbitmq:5672/
    depends_on:
      - postgres
      - redis
      - rabbitmq
    networks:
      - streamflow-network
    volumes:
      - ./logs:/app/logs
      - ./config:/app/config

volumes:
  postgres_data:
  redis_data:
  rabbitmq_data:

networks:
  streamflow-network:
    driver: bridge
"""
        
        with open(project_path / "docker-compose.yml", "w") as f:
            f.write(compose_content)
    
    def _create_env_file(self, project_path: Path) -> None:
        """Create .env file"""
        env_content = """# StreamFlow Environment Configuration

# Core Configuration
ENVIRONMENT=development
LOG_LEVEL=INFO
DEBUG=true

# Database Configuration
DB_HOST=localhost
DB_PORT=5432
DB_NAME=streamflow
DB_USER=streamflow
DB_PASSWORD=streamflow123

# Redis Configuration
REDIS_HOST=localhost
REDIS_PORT=6379

# RabbitMQ Configuration
RABBITMQ_HOST=localhost
RABBITMQ_PORT=5672
RABBITMQ_USER=admin
RABBITMQ_PASSWORD=admin123

# Security Configuration
JWT_SECRET_KEY=your-secret-key-change-in-production
CORS_ORIGINS=http://localhost:3001,http://localhost:8080

# Service Ports
INGESTION_PORT=8001
ANALYTICS_PORT=8002
ALERTING_PORT=8003
STORAGE_PORT=8004
DASHBOARD_PORT=8005
"""
        
        with open(project_path / ".env", "w") as f:
            f.write(env_content)
    
    def _create_readme(self, project_path: Path, project_name: str) -> None:
        """Create project README"""
        readme_content = f"""# {project_name.title()}

StreamFlow Analytics Project

## Quick Start

```bash
# Start the platform
streamflow start

# View dashboard
open http://localhost:3001

# Send test event
curl -X POST http://localhost:8001/events \\
  -H "Content-Type: application/json" \\
  -d '{{"type": "web.click", "source": "web-app", "user_id": "user123"}}'
```

## Services

- **Dashboard**: http://localhost:3001
- **API Gateway**: http://localhost:8005
- **Grafana**: http://localhost:3000
- **RabbitMQ**: http://localhost:15672

## Configuration

Edit `config/config.json` to customize your setup.

## Documentation

See [StreamFlow Documentation](https://docs.streamflow.io) for more details.
"""
        
        with open(project_path / "README.md", "w") as f:
            f.write(readme_content)


@click.group()
@click.version_option(version="0.1.0")
def cli():
    """🌊 StreamFlow - Enterprise-Grade Real-Time Analytics Platform"""
    pass


@cli.command()
@click.argument("project_name")
@click.option("--template", default="basic", help="Project template (basic, advanced, enterprise)")
def init(project_name: str, template: str):
    """Initialize a new StreamFlow project"""
    console.print(Panel.fit(
        f"🌊 [bold blue]StreamFlow[/bold blue] - Initializing project: [green]{project_name}[/green]",
        border_style="blue"
    ))
    
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        task = progress.add_task("Creating project structure...", total=None)
        
        try:
            cli_instance = StreamFlowCLI()
            cli_instance.create_project_structure(project_name)
            
            progress.update(task, description="✅ Project created successfully!")
            
            console.print(f"\n[green]✅ Project '{project_name}' created successfully![/green]")
            console.print(f"\n[bold]Next steps:[/bold]")
            console.print(f"  1. cd {project_name}")
            console.print(f"  2. streamflow start")
            console.print(f"  3. Open http://localhost:3001")
            
        except Exception as e:
            progress.update(task, description=f"❌ Error: {e}")
            console.print(f"[red]❌ Error creating project: {e}[/red]")
            sys.exit(1)


@cli.command()
@click.option("--detach", "-d", is_flag=True, help="Run in background")
@click.option("--services", multiple=True, help="Specific services to start")
def start(detach: bool, services: List[str]):
    """Start StreamFlow services"""
    console.print(Panel.fit(
        "🚀 [bold green]Starting StreamFlow Services[/bold green]",
        border_style="green"
    ))
    
    if not Path("docker-compose.yml").exists():
        console.print("[red]❌ No docker-compose.yml found. Run 'streamflow init' first.[/red]")
        sys.exit(1)
    
    cmd = ["docker-compose", "up"]
    if detach:
        cmd.append("-d")
    if services:
        cmd.extend(services)
    
    try:
        subprocess.run(cmd, check=True)
        if detach:
            console.print("\n[green]✅ StreamFlow started successfully![/green]")
            console.print("\n[bold]Access your services:[/bold]")
            console.print("  📊 Dashboard: http://localhost:3001")
            console.print("  📈 Grafana: http://localhost:3000")
            console.print("  🐰 RabbitMQ: http://localhost:15672")
    except subprocess.CalledProcessError as e:
        console.print(f"[red]❌ Error starting services: {e}[/red]")
        sys.exit(1)


@cli.command()
@click.option("--remove-volumes", is_flag=True, help="Remove volumes")
def stop(remove_volumes: bool):
    """Stop StreamFlow services"""
    console.print(Panel.fit(
        "🛑 [bold red]Stopping StreamFlow Services[/bold red]",
        border_style="red"
    ))
    
    cmd = ["docker-compose", "down"]
    if remove_volumes:
        cmd.extend(["-v", "--remove-orphans"])
    
    try:
        subprocess.run(cmd, check=True)
        console.print("[green]✅ StreamFlow stopped successfully![/green]")
    except subprocess.CalledProcessError as e:
        console.print(f"[red]❌ Error stopping services: {e}[/red]")
        sys.exit(1)


@cli.command()
def status():
    """Show status of StreamFlow services"""
    console.print(Panel.fit(
        "📊 [bold blue]StreamFlow Services Status[/bold blue]",
        border_style="blue"
    ))
    
    try:
        result = subprocess.run(
            ["docker-compose", "ps", "--format", "json"],
            capture_output=True,
            text=True,
            check=True
        )
        
        if result.stdout.strip():
            services = json.loads(result.stdout) if result.stdout.strip().startswith('[') else [json.loads(line) for line in result.stdout.strip().split('\n')]
            
            table = Table(show_header=True, header_style="bold blue")
            table.add_column("Service", style="cyan")
            table.add_column("Status", style="green")
            table.add_column("Ports", style="yellow")
            
            for service in services:
                status_text = "🟢 Running" if service.get("State") == "running" else "🔴 Stopped"
                ports = service.get("Publishers", [])
                port_text = ", ".join([f"{p.get('PublishedPort', '')}->{p.get('TargetPort', '')}" for p in ports]) if ports else "-"
                
                table.add_row(
                    service.get("Service", "Unknown"),
                    status_text,
                    port_text
                )
            
            console.print(table)
        else:
            console.print("[yellow]⚠️ No services are currently running[/yellow]")
            
    except subprocess.CalledProcessError:
        console.print("[red]❌ Error getting service status[/red]")
    except (json.JSONDecodeError, KeyError):
        console.print("[yellow]⚠️ Unable to parse service status[/yellow]")


@cli.command()
@click.option("--tail", "-f", is_flag=True, help="Follow log output")
@click.option("--lines", "-n", default=100, help="Number of lines to show")
@click.argument("service", required=False)
def logs(tail: bool, lines: int, service: Optional[str]):
    """View service logs"""
    cmd = ["docker-compose", "logs"]
    
    if tail:
        cmd.append("-f")
    cmd.extend(["--tail", str(lines)])
    
    if service:
        cmd.append(service)
    
    try:
        subprocess.run(cmd, check=True)
    except subprocess.CalledProcessError as e:
        console.print(f"[red]❌ Error viewing logs: {e}[/red]")
        sys.exit(1)


@cli.command()
@click.argument("event_type")
@click.option("--source", default="cli", help="Event source")
@click.option("--user-id", help="User ID")
@click.option("--data", help="Event data as JSON string")
def send_event(event_type: str, source: str, user_id: Optional[str], data: Optional[str]):
    """Send a test event to StreamFlow"""
    import httpx
    
    event_data = {
        "type": event_type,
        "source": source,
        "data": json.loads(data) if data else {},
    }
    
    if user_id:
        event_data["user_id"] = user_id
    
    try:
        with httpx.Client() as client:
            response = client.post(
                "http://localhost:8001/events",
                json=event_data,
                timeout=10
            )
            response.raise_for_status()
            
            console.print(f"[green]✅ Event sent successfully![/green]")
            console.print(f"Response: {response.json()}")
            
    except httpx.RequestError as e:
        console.print(f"[red]❌ Error sending event: {e}[/red]")
        console.print("[yellow]💡 Make sure StreamFlow is running: streamflow start[/yellow]")
    except httpx.HTTPStatusError as e:
        console.print(f"[red]❌ HTTP error {e.response.status_code}: {e.response.text}[/red]")


@cli.command()
def dashboard():
    """Open the StreamFlow dashboard in browser"""
    import webbrowser
    
    url = "http://localhost:3001"
    console.print(f"🌐 Opening dashboard: {url}")
    webbrowser.open(url)


@cli.command()
def docs():
    """Open StreamFlow documentation"""
    import webbrowser
    
    url = "https://docs.streamflow.io"
    console.print(f"📚 Opening documentation: {url}")
    webbrowser.open(url)


def main():
    """Main CLI entry point"""
    try:
        cli()
    except KeyboardInterrupt:
        console.print("\n[yellow]⚠️ Operation cancelled by user[/yellow]")
        sys.exit(1)
    except Exception as e:
        console.print(f"[red]❌ Unexpected error: {e}[/red]")
        sys.exit(1)


if __name__ == "__main__":
    main()
