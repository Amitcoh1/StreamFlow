.PHONY: help install dev test lint format clean build docker run stop logs migrate seed

# Default target
help:
	@echo "StreamFlow Development Commands"
	@echo "==============================="
	@echo "install     - Install dependencies"
	@echo "dev         - Start development environment"
	@echo "test        - Run tests"
	@echo "test-cov    - Run tests with coverage"
	@echo "lint        - Run linting"
	@echo "format      - Format code"
	@echo "clean       - Clean temporary files"
	@echo "build       - Build Docker images"
	@echo "docker      - Start with Docker Compose"
	@echo "run         - Run specific service"
	@echo "stop        - Stop all services"
	@echo "logs        - View logs"
	@echo "migrate     - Run database migrations"
	@echo "seed        - Seed database with sample data"

# Install dependencies
install:
	pip install -r requirements.txt
	pip install -e .

# Development environment
dev:
	@echo "Starting StreamFlow development environment..."
	docker-compose up -d postgres redis rabbitmq
	@echo "Waiting for services to be ready..."
	sleep 10
	python -m services.dashboard.main

# Testing
test:
	pytest tests/ -v

test-cov:
	pytest tests/ -v --cov=shared --cov=services --cov-report=html --cov-report=term

test-unit:
	pytest tests/unit/ -v

test-integration:
	pytest tests/integration/ -v

test-performance:
	pytest tests/performance/ -v

# Code quality
lint:
	black --check .
	isort --check-only .
	mypy shared/ services/

format:
	black .
	isort .

# Cleanup
clean:
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	rm -rf .coverage htmlcov/ .pytest_cache/

# Docker operations
build:
	docker-compose build

docker:
	docker-compose up -d

docker-dev:
	docker-compose -f docker-compose.yml -f docker-compose.dev.yml up -d

stop:
	docker-compose down

stop-all:
	docker-compose down -v --remove-orphans

logs:
	docker-compose logs -f

logs-service:
	@read -p "Enter service name: " service; \
	docker-compose logs -f $$service

# Database operations
migrate:
	@echo "Running database migrations..."
	alembic upgrade head

migrate-create:
	@read -p "Enter migration message: " message; \
	alembic revision --autogenerate -m "$$message"

migrate-down:
	alembic downgrade -1

seed:
	@echo "Seeding database with sample data..."
	python scripts/seed_database.py

# Service operations
run-dashboard:
	python -m services.dashboard.main

run-ingestion:
	python -m services.ingestion.main

run-analytics:
	python -m services.analytics.main

run-alerting:
	python -m services.alerting.main

run-storage:
	python -m services.storage.main

# Monitoring
metrics:
	curl http://localhost:9090/metrics

health:
	@echo "Checking service health..."
	@curl -s http://localhost:8004/health | python -m json.tool || echo "Dashboard service not available"
	@curl -s http://localhost:8001/health | python -m json.tool || echo "Ingestion service not available"
	@curl -s http://localhost:8002/health | python -m json.tool || echo "Analytics service not available"
	@curl -s http://localhost:8003/health | python -m json.tool || echo "Alerting service not available"
	@curl -s http://localhost:8005/health | python -m json.tool || echo "Storage service not available"

# Environment setup
setup-env:
	cp .env.example .env
	@echo "Environment file created. Please update .env with your settings."

setup-hooks:
	pre-commit install

# Security
security-scan:
	bandit -r shared/ services/

dependency-check:
	safety check

# Performance
load-test:
	@echo "Running load tests..."
	python tests/performance/load_test.py

benchmark:
	python tests/performance/benchmark.py

# Documentation
docs:
	@echo "Generating documentation..."
	python -m pydoc -w shared services

docs-serve:
	python -m http.server 8080 -d docs/

# Deployment
deploy-staging:
	@echo "Deploying to staging..."
	docker-compose -f docker-compose.staging.yml up -d

deploy-prod:
	@echo "Deploying to production..."
	docker-compose -f docker-compose.prod.yml up -d

# Backup
backup-db:
	@echo "Creating database backup..."
	docker-compose exec postgres pg_dump -U streamflow streamflow > backup_$(shell date +%Y%m%d_%H%M%S).sql

restore-db:
	@read -p "Enter backup file path: " backup_file; \
	docker-compose exec -T postgres psql -U streamflow streamflow < $$backup_file

# Development utilities
shell:
	python -c "from shared.utils.config import get_settings; print('StreamFlow Shell Ready'); import IPython; IPython.embed()"

jupyter:
	jupyter lab --ip=0.0.0.0 --port=8888 --no-browser --allow-root

# CI/CD helpers
ci-test:
	pytest tests/ -v --junitxml=test-results.xml --cov=shared --cov=services --cov-report=xml

ci-build:
	docker build -t streamflow:$(shell git rev-parse --short HEAD) .

ci-security:
	bandit -r shared/ services/ -f json -o security-report.json

# Quick start
quick-start: setup-env install build docker migrate seed
	@echo "StreamFlow is ready! Visit http://localhost:8004"

# Full reset
reset: stop-all clean
	docker system prune -f
	docker volume prune -f