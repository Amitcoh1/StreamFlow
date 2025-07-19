# 🔧 StreamFlow with Your Existing Infrastructure

## Using StreamFlow pip package with your own RabbitMQ, PostgreSQL, and Redis

If you already have the required infrastructure running, here's how to configure StreamFlow to use it:

---

## 📋 **Prerequisites**

Your infrastructure must have:
- 🐰 **RabbitMQ** (any version 3.8+)
- 🐘 **PostgreSQL** (version 12+)
- 🔴 **Redis** (version 6+)

---

## ⚙️ **Configuration Methods**

StreamFlow supports **3 ways** to configure your infrastructure:

### 1. **Environment Variables (Recommended)**

Create a `.env` file in your project directory:

```bash
# .env file
# RabbitMQ Configuration
RABBITMQ_URL=amqp://myuser:mypass@your-rabbitmq-server:5672/myvhost
RABBITMQ_EXCHANGE_EVENTS=streamflow_events
RABBITMQ_EXCHANGE_ANALYTICS=streamflow_analytics
RABBITMQ_EXCHANGE_ALERTS=streamflow_alerts

# PostgreSQL Configuration  
DATABASE_URL=postgresql+asyncpg://dbuser:dbpass@your-postgres-server:5432/streamflow_db
DATABASE_ECHO=false
DATABASE_POOL_SIZE=10

# Redis Configuration
REDIS_URL=redis://your-redis-server:6379/0
REDIS_DB=0

# Security (Required)
JWT_SECRET_KEY=your-super-secret-jwt-key-at-least-32-characters-long
JWT_ALGORITHM=HS256

# Service Ports (Optional - if you want custom ports)
INGESTION_PORT=8001
DASHBOARD_PORT=8004
STORAGE_PORT=8005
```

### 2. **System Environment Variables**

```bash
# Export environment variables
export RABBITMQ_URL="amqp://myuser:mypass@your-rabbitmq-server:5672/myvhost"
export DATABASE_URL="postgresql+asyncpg://dbuser:dbpass@your-postgres-server:5432/streamflow_db"
export REDIS_URL="redis://your-redis-server:6379/0"
export JWT_SECRET_KEY="your-super-secret-jwt-key-at-least-32-characters-long"
```

### 3. **Configuration File**

Create a `config.py` file:

```python
# config.py
import os
from streamflow.shared.config import Settings

# Override default settings
os.environ.update({
    "RABBITMQ_URL": "amqp://myuser:mypass@your-rabbitmq-server:5672/myvhost",
    "DATABASE_URL": "postgresql+asyncpg://dbuser:dbpass@your-postgres-server:5432/streamflow_db",
    "REDIS_URL": "redis://your-redis-server:6379/0",
    "JWT_SECRET_KEY": "your-super-secret-jwt-key-at-least-32-characters-long"
})
```

---

## 🚀 **Step-by-Step Setup**

### Step 1: Install StreamFlow
```bash
pip install streamflow
```

### Step 2: Configure Your Infrastructure

**Example with existing AWS RDS and ElastiCache:**

```bash
# .env file for AWS setup
RABBITMQ_URL=amqp://admin:password123@your-rabbitmq.amazonaws.com:5672/prod
DATABASE_URL=postgresql+asyncpg://streamflow_user:secure_pass@your-rds.amazonaws.com:5432/streamflow_prod
REDIS_URL=redis://your-elasticache.cache.amazonaws.com:6379/0
JWT_SECRET_KEY=aws-production-jwt-secret-key-super-secure-32-chars
```

**Example with local infrastructure:**

```bash
# .env file for local setup
RABBITMQ_URL=amqp://streamflow:streamflow123@192.168.1.100:5672/streamflow
DATABASE_URL=postgresql+asyncpg://streamflow_user:streamflow_pass@192.168.1.101:5432/streamflow
REDIS_URL=redis://192.168.1.102:6379/1
JWT_SECRET_KEY=local-dev-secret-key-minimum-32-characters
```

### Step 3: Initialize Database
```bash
# Create database tables
streamflow init-db

# Verify connection
streamflow health
```

### Step 4: Test the Setup
```bash
# Send a test event
streamflow send-event --type web.click --count 1

# Check status
streamflow status
```

---

## 📝 **Real-World Configuration Examples**

### Production AWS Setup
```bash
# Production environment with AWS services
RABBITMQ_URL=amqps://prod-user:complex-password@prod-rabbitmq.company.com:5671/production
DATABASE_URL=postgresql+asyncpg://streamflow_prod:super-secure-db-pass@rds-prod.us-east-1.rds.amazonaws.com:5432/streamflow_production
REDIS_URL=rediss://elasticache-prod.cache.amazonaws.com:6380/0
JWT_SECRET_KEY=production-jwt-secret-key-with-high-entropy-64-characters-long
DATABASE_POOL_SIZE=20
REDIS_MAX_CONNECTIONS=50
```

### Docker Compose with External Services
```bash
# Using external managed services with Docker containers
RABBITMQ_URL=amqp://user:pass@external-rabbitmq.company.com:5672/streamflow
DATABASE_URL=postgresql+asyncpg://app_user:app_pass@db.company.com:5432/analytics
REDIS_URL=redis://cache.company.com:6379/2
JWT_SECRET_KEY=company-streamflow-jwt-secret-key-production-grade
```

### Development with Local Services
```bash
# Local development setup
RABBITMQ_URL=amqp://dev:dev123@localhost:5672/dev
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/streamflow_dev
REDIS_URL=redis://localhost:6379/0
JWT_SECRET_KEY=development-jwt-key-for-local-testing-only-32-chars
DATABASE_ECHO=true
LOG_LEVEL=DEBUG
```

---

## 🔐 **Security Considerations**

### Required Security Settings
```bash
# Always set these for production
JWT_SECRET_KEY=your-cryptographically-secure-secret-key-minimum-32-characters
JWT_ALGORITHM=HS256
JWT_EXPIRE_MINUTES=30
BCRYPT_ROUNDS=12
```

### Database Security
```bash
# Use connection pooling and SSL
DATABASE_URL=postgresql+asyncpg://user:pass@host:5432/db?sslmode=require
DATABASE_POOL_SIZE=10
DATABASE_MAX_OVERFLOW=20
```

### RabbitMQ Security  
```bash
# Use secure connections in production
RABBITMQ_URL=amqps://user:pass@host:5671/vhost
RABBITMQ_HEARTBEAT=600
```

---

## 🧪 **Testing Your Configuration**

### 1. Test Connection
```python
# test_config.py
import asyncio
from streamflow.shared.config import get_settings
from streamflow.shared.messaging import get_message_broker
from streamflow.shared.database import get_database_manager

async def test_connections():
    settings = get_settings()
    print(f"RabbitMQ URL: {settings.rabbitmq.url}")
    print(f"Database URL: {settings.database.url}")
    print(f"Redis URL: {settings.redis.url}")
    
    # Test RabbitMQ
    try:
        broker = await get_message_broker()
        print("✅ RabbitMQ connection successful")
    except Exception as e:
        print(f"❌ RabbitMQ connection failed: {e}")
    
    # Test Database
    try:
        db = await get_database_manager()
        print("✅ Database connection successful")
    except Exception as e:
        print(f"❌ Database connection failed: {e}")

asyncio.run(test_connections())
```

### 2. Test Event Flow
```python
# test_events.py
import asyncio
from streamflow.shared.models import Event, EventType
from streamflow.shared.messaging import get_event_publisher

async def test_event_flow():
    publisher = await get_event_publisher()
    
    event = Event(
        type=EventType.WEB_CLICK,
        source="test-app",
        data={"test": True, "timestamp": "2024-01-15T10:30:00Z"}
    )
    
    await publisher.publish_event(event)
    print(f"✅ Event published: {event.id}")

asyncio.run(test_event_flow())
```

---

## 🎯 **Usage After Configuration**

Once configured, you can use StreamFlow exactly as documented:

```bash
# All CLI commands now work
streamflow send-event --type user.login --count 10
streamflow start --service ingestion --port 8001
streamflow start --service analytics
streamflow status
```

```python
# All Python APIs work
import asyncio
from streamflow.shared.models import Event, EventType
from streamflow.shared.messaging import get_event_publisher

async def my_app():
    publisher = await get_event_publisher()
    
    # Send events from your application
    await publisher.publish_event(Event(
        type=EventType.API_REQUEST,
        source="my-microservice",
        data={"endpoint": "/api/users", "status": 200}
    ))

asyncio.run(my_app())
```

---

## 🆘 **Troubleshooting**

### Common Issues

**Connection Refused:**
```bash
# Check if services are running
telnet your-rabbitmq-server 5672
telnet your-postgres-server 5432
telnet your-redis-server 6379
```

**Authentication Failed:**
```bash
# Verify credentials
streamflow health
# Check logs for detailed error messages
```

**Database Not Found:**
```bash
# Create database first
createdb -h your-postgres-server -U postgres streamflow_db
```

**Permission Denied:**
```bash
# Grant permissions
GRANT ALL PRIVILEGES ON DATABASE streamflow_db TO streamflow_user;
```

---

## 💡 **Pro Tips**

1. **Use different databases for different environments:**
   ```bash
   # Development
   DATABASE_URL=postgresql+asyncpg://user:pass@localhost:5432/streamflow_dev
   
   # Staging  
   DATABASE_URL=postgresql+asyncpg://user:pass@staging-db:5432/streamflow_staging
   
   # Production
   DATABASE_URL=postgresql+asyncpg://user:pass@prod-db:5432/streamflow_prod
   ```

2. **Use Redis namespaces:**
   ```bash
   # Different Redis databases for different environments
   REDIS_URL=redis://redis-server:6379/0  # Production
   REDIS_URL=redis://redis-server:6379/1  # Staging
   REDIS_URL=redis://redis-server:6379/2  # Development
   ```

3. **Monitor connections:**
   ```bash
   # Set appropriate pool sizes based on your load
   DATABASE_POOL_SIZE=20
   RABBITMQ_MAX_CONNECTIONS=30
   REDIS_MAX_CONNECTIONS=25
   ```

**🎉 You're now ready to use StreamFlow with your existing infrastructure!**