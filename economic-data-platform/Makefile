# =============================================================================
# Economic Data Platform - Makefile
# =============================================================================

.PHONY: help install dev-setup docker-up docker-down docker-logs clean test lint format migrate dbt-run api-dev ui-dev quality

# Default target
help:
	@echo "Economic Data Platform - Available Commands:"
	@echo ""
	@echo "Setup & Installation:"
	@echo "  make install          Install Python dependencies"
	@echo "  make dev-setup        Complete development environment setup"
	@echo ""
	@echo "Docker Commands:"
	@echo "  make docker-up        Start infra services (Postgres, ClickHouse, Redis, Kafka, MinIO, Monitoring)"
	@echo "  make docker-up-full   Start all services including API + Airflow + Trino"
	@echo "  make docker-down      Stop all Docker services"
	@echo "  make docker-logs      View Docker logs"
	@echo "  make docker-clean     Remove all Docker volumes and containers"
	@echo ""
	@echo "Database:"
	@echo "  make migrate          Run database migrations (PostgreSQL DDL)"
	@echo "  make seed             Seed database via dbt seeds"
	@echo "  make migrate-docker   Run migrations inside Docker container"
	@echo ""
	@echo "dbt Commands:"
	@echo "  make dbt-run          Run dbt models"
	@echo "  make dbt-test         Run dbt tests"
	@echo "  make dbt-docs         Generate and serve dbt documentation"
	@echo ""
	@echo "API:"
	@echo "  make api-dev          Start FastAPI in development mode (port 8000)"
	@echo "  make api-prod         Start FastAPI in production mode (4 workers)"
	@echo ""
	@echo "Frontend:"
	@echo "  make ui-dev           Start Next.js UI in development mode (port 3000)"
	@echo "  make ui-build         Build Next.js UI for production"
	@echo ""
	@echo "Data Ingestion:"
	@echo "  make ingest-olist     Run Olist e-commerce CSV ingestion"
	@echo "  make ingest-crypto    Run crypto data ingestion"
	@echo "  make ingest-econ      Run economic data ingestion"
	@echo "  make ingest-all       Run all data ingestion"
	@echo ""
	@echo "Data Quality:"
	@echo "  make quality-olist    Run Great Expectations on Olist bronze tables"
	@echo "  make quality-mssql    Run Great Expectations on MSSQL bronze tables"
	@echo "  make quality-all      Run all data quality checks"
	@echo ""
	@echo "Testing & Code Quality:"
	@echo "  make test             Run all tests"
	@echo "  make test-api         Run API router tests"
	@echo "  make test-dags        Run Airflow DAG integrity tests"
	@echo "  make test-transform   Run dbt model structure tests"
	@echo "  make test-quality     Run data quality tests"
	@echo "  make lint             Run linters (flake8 + isort + black)"
	@echo "  make format           Auto-format code"
	@echo "  make type-check       Run mypy type checking"
	@echo ""
	@echo "Monitoring:"
	@echo "  make grafana-open     Open Grafana in browser"
	@echo "  make prometheus-open  Open Prometheus in browser"

# =============================================================================
# Setup & Installation
# =============================================================================

install:
	pip install --upgrade pip
	pip install -r requirements.txt
	pre-commit install

dev-setup: install
	cp -n .env.example .env || true
	@echo "Development environment setup complete!"
	@echo "Please edit .env with your API keys"

# =============================================================================
# Docker Commands
# =============================================================================

docker-up:
	docker-compose up -d

docker-up-full:
	docker-compose --profile api --profile airflow up -d

docker-down:
	docker-compose down

docker-logs:
	docker-compose logs -f

docker-clean:
	docker-compose down -v --remove-orphans
	docker system prune -f

docker-rebuild:
	docker-compose build --no-cache
	docker-compose up -d

# =============================================================================
# Database
# =============================================================================

migrate:
	@echo "Running database migrations..."
	@for f in sql/postgres/0*.sql; do echo "  → $$f"; psql "$(DATABASE_URL)" -f "$$f" 2>/dev/null || PGPASSWORD=$(POSTGRES_PASSWORD) psql -h localhost -U $(POSTGRES_USER) -d $(POSTGRES_DB) -f "$$f"; done
	@echo "Migrations complete!"

migrate-docker:
	@echo "Running migrations inside Docker..."
	docker exec -i economic-postgres psql -U $${POSTGRES_USER:-economic_user} -d $${POSTGRES_DB:-economic_data} < sql/postgres/01_bronze_schema.sql
	docker exec -i economic-postgres psql -U $${POSTGRES_USER:-economic_user} -d $${POSTGRES_DB:-economic_data} < sql/postgres/02_silver_schema.sql
	docker exec -i economic-postgres psql -U $${POSTGRES_USER:-economic_user} -d $${POSTGRES_DB:-economic_data} < sql/postgres/03_gold_crypto.sql
	docker exec -i economic-postgres psql -U $${POSTGRES_USER:-economic_user} -d $${POSTGRES_DB:-economic_data} < sql/postgres/04_gold_economic.sql
	docker exec -i economic-postgres psql -U $${POSTGRES_USER:-economic_user} -d $${POSTGRES_DB:-economic_data} < sql/postgres/05_gold_combined.sql
	docker exec -i economic-postgres psql -U $${POSTGRES_USER:-economic_user} -d $${POSTGRES_DB:-economic_data} < sql/postgres/06_bronze_olist.sql
	docker exec -i economic-postgres psql -U $${POSTGRES_USER:-economic_user} -d $${POSTGRES_DB:-economic_data} < sql/postgres/07_bronze_mssql.sql
	@echo "Docker migrations complete!"

seed:
	@echo "Seeding via dbt seeds..."
	cd $(DBT_PROJECT_DIR) && dbt seed

# =============================================================================
# dbt Commands
# =============================================================================

DBT_PROJECT_DIR=dbt

dbt-run:
	cd $(DBT_PROJECT_DIR) && dbt run

dbt-test:
	cd $(DBT_PROJECT_DIR) && dbt test

dbt-docs:
	cd $(DBT_PROJECT_DIR) && dbt docs generate
	cd $(DBT_PROJECT_DIR) && dbt docs serve

dbt-clean:
	cd $(DBT_PROJECT_DIR) && dbt clean

dbt-debug:
	cd $(DBT_PROJECT_DIR) && dbt debug

# =============================================================================
# API
# =============================================================================

api-dev:
	uvicorn src.api.main:app --reload --host 0.0.0.0 --port 8000

api-prod:
	uvicorn src.api.main:app --host 0.0.0.0 --port 8000 --workers 4

# =============================================================================
# Data Ingestion
# =============================================================================

ingest-crypto:
	@echo "Running crypto data ingestion..."
	python -c "from ingestion.custom.api.crypto.coingecko_client import CoinGeckoClient; c = CoinGeckoClient(); print(c.get_top_coins(limit=5))"

ingest-econ:
	@echo "Running economic data ingestion..."
	python -c "from ingestion.custom.api.economic.fred_client import FredClient; c = FredClient(); print(c.health_check())"

ingest-olist:
	@echo "Running Olist e-commerce CSV ingestion..."
	python -m ingestion.custom.api.ecommerce.ingest_csv

ingest-all: ingest-olist ingest-crypto ingest-econ
	@echo "All data ingestion completed!"

stream-start:
	@echo "Starting real-time streaming..."
	python -c "from ingestion.custom.api.crypto.binance_websocket import BinanceWebSocket; ws = BinanceWebSocket(); ws.start()"

# =============================================================================
# Frontend (Next.js UI)
# =============================================================================

ui-dev:
	cd ui && npm run dev

ui-build:
	cd ui && npm run build

ui-lint:
	cd ui && npm run lint

# =============================================================================
# Data Quality (Great Expectations)
# =============================================================================

quality-olist:
	python data_quality/great_expectations/run_checkpoint.py --suite olist_bronze_suite

quality-mssql:
	python data_quality/great_expectations/run_checkpoint.py --suite mssql_bronze_suite

quality-all: quality-olist quality-mssql
	@echo "All quality checks completed!"

# =============================================================================
# Testing & Quality
# =============================================================================

test:
	pytest tests/ -v --cov=src --cov-report=term-missing

test-api:
	pytest tests/test_api/ -v

test-dags:
	pytest tests/test_dags/ -v

test-transform:
	pytest tests/test_transform/ -v

test-quality:
	pytest tests/test_quality/ -v

lint:
	flake8 src/ tests/
	isort --check-only src/ tests/
	black --check src/ tests/

format:
	isort src/ tests/
	black src/ tests/

type-check:
	mypy src/ --ignore-missing-imports

# =============================================================================
# Monitoring
# =============================================================================

grafana-open:
	@echo "Opening Grafana at http://localhost:3001"
	@open http://localhost:3001 2>/dev/null || start http://localhost:3001 2>/dev/null || xdg-open http://localhost:3001 || python -m webbrowser "http://localhost:3001"

prometheus-open:
	@echo "Opening Prometheus at http://localhost:9090"
	@open http://localhost:9090 2>/dev/null || start http://localhost:9090 2>/dev/null || xdg-open http://localhost:9090 || python -m webbrowser "http://localhost:9090"

# =============================================================================
# Utilities
# =============================================================================

clean:
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".mypy_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	rm -rf build/ dist/ .eggs/
	rm -rf htmlcov/ .coverage coverage.xml

docs:
	cd $(DBT_PROJECT_DIR) && dbt docs generate
	@echo "dbt docs generated. Run 'make docs-serve' to view."

docs-serve:
	cd $(DBT_PROJECT_DIR) && dbt docs serve

# =============================================================================
# Jupyter
# =============================================================================

notebook:
	jupyter lab --notebook-dir=notebooks

# =============================================================================
# Spark
# =============================================================================

# Spark jobs (requires PySpark installed and spark/ directory populated)
spark-submit-crypto:
	@echo "Spark jobs are optional — dbt handles transformations."
	@echo "To enable, add Spark job scripts to spark/jobs/ and update this target."

spark-submit-econ:
	@echo "Spark jobs are optional — dbt handles transformations."
	@echo "To enable, add Spark job scripts to spark/jobs/ and update this target."


