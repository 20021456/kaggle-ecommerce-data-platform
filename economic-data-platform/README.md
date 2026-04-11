# Economic Data Analytics Platform

A **Multi-Domain Data Analytics Platform** built on medallion architecture combining:

- **E-Commerce Analytics** — Brazilian Olist dataset (100k+ orders, RFM segmentation, logistics)
- **Crypto/Financial Markets** — Binance, CoinGecko, CryptoCompare, Blockchain.info, Fear&Greed
- **Economic Indicators** — FRED, BEA, BLS, Treasury, World Bank, IMF, OECD
- **Business Intelligence** — MSSQL enterprise data (45.124.94.158)

## Architecture

```
┌──────────────────────────────────────────────────────────────────────┐
│                        DATA SOURCES                                  │
│  Olist CSV  │  MSSQL  │  20+ APIs (crypto, economic, international) │
└──────┬──────┴────┬────┴──────────────┬───────────────────────────────┘
       │           │                   │
       ▼           ▼                   ▼
┌──────────────────────────────────────────────────────────────────────┐
│ INGESTION LAYER                                                      │
│  Python clients (BaseAPIClient) │ Airflow DAGs │ Kafka streaming    │
└──────┬──────────────────────────┴──────┬────────┴────────────────────┘
       │                                 │
       ▼                                 ▼
┌──────────────────────────────────────────────────────────────────────┐
│ STORAGE                                                              │
│  PostgreSQL 16 (Bronze → Silver → Gold)  │  ClickHouse (OLAP)       │
│  MinIO (S3-compatible data lake)         │  Redis (cache/checkpoint) │
└──────┬───────────────────────────────────┴───────────────────────────┘
       │
       ▼
┌──────────────────────────────────────────────────────────────────────┐
│ TRANSFORMATION                                                       │
│  dbt (staging → intermediate → marts)  │  Spark (batch jobs)         │
│  Trino (federated SQL across PG + CH + MinIO)                        │
└──────┬───────────────────────────────────────────────────────────────┘
       │
       ▼
┌──────────────────────────────────────────────────────────────────────┐
│ SERVING & UI                                                         │
│  FastAPI REST API (8 routers, 21+ endpoints)                         │
│  Next.js 16 Dashboard (Airflow monitor, Ingestion monitor, Analytics)│
│  Grafana (3 dashboards: pipeline health, freshness, quality)         │
└──────────────────────────────────────────────────────────────────────┘
```

## Project Structure

```
economic-data-platform/
├── src/                         # FastAPI backend + shared Python library
│   ├── api/                     # FastAPI app (8 routers, 21+ endpoints)
│   │   ├── routers/             # crypto, economic, analytics, health,
│   │   │                        # monitor, ingestion, dashboard, query
│   │   ├── config.py            # API + Airflow + Trino settings
│   │   └── main.py              # App factory, middleware, router registration
│   ├── data_platform/           # Shared installable lib (pip install -e src/)
│   ├── models/schemas.py        # Pydantic models
│   └── utils/                   # Logger, metrics (Prometheus), helpers
├── ui/                          # Next.js 16 frontend (App Router + shadcn/ui)
│   ├── app/monitor/airflow/     # Airflow DAG monitor page
│   ├── app/monitor/ingestion/   # Data source health page
│   ├── app/dashboard/           # E-commerce analytics dashboard (Recharts)
│   └── lib/api.ts               # Typed API client
├── airflow/                     # Orchestration
│   ├── dags/ingestion/          # olist_ingestion, mssql_ingestion, etl_daily
│   ├── dags/transformation/     # dbt_olist_dag
│   ├── dags/export/             # mart_export_dag
│   ├── dags/maintenance/        # data_quality_dag
│   └── common/                  # default_args + callbacks (Slack + email)
├── dbt/                         # SQL transformations (staging → intermediate → marts)
├── ingestion/                   # 20+ data source connectors
│   └── custom/api/              # BaseAPIClient, crypto/, economic/, ecommerce/
├── sql/postgres/                # DDL: 01_bronze → 05_gold_combined
├── sql/clickhouse/              # ClickHouse DDL: databases, tables, Kafka
├── trino/                       # Trino config (catalogs: PG, CH, MinIO/Hive)
├── monitoring/                  # Prometheus + Grafana
│   ├── alerts/                  # 10 pipeline + infra alert rules
│   └── dashboards/grafana/      # pipeline_health, data_freshness, data_quality
├── data_quality/                # Great Expectations suites + runner
├── infra/                       # Docker, Terraform, Kubernetes, CI/CD
├── dokploy/                     # Dokploy deployment configs
├── tests/                       # DAG integrity, API, query validation, GE suites
├── docker-compose.yml           # Full local stack (12 services)
└── Makefile                     # 30+ convenience commands
```

## Quick Start

### Prerequisites

- Python 3.11+, Node.js 18+, Docker & Docker Compose

### Installation

```bash
# Clone and setup
git clone <repo-url> && cd economic-data-platform

# Python environment
python -m venv venv && source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
pip install -e src/  # Install shared library

# Environment
cp .env.example .env  # Edit with your API keys

# Start infrastructure
make docker-up        # Postgres, ClickHouse, Redis, Kafka, MinIO, Prometheus, Grafana
docker compose --profile trino up -d  # Optional: Trino + Hive Metastore

# Initialize database
# DDL auto-runs from sql/postgres/ on first Postgres startup

# Start services
make api-dev          # FastAPI on :8000
make ui-dev           # Next.js on :3000 (in separate terminal)
```

### With Airflow

```bash
docker compose --profile airflow up -d
# Access Airflow UI: http://localhost:8080
```

## API Endpoints (21+)

| Group | Prefix | Endpoints |
|-------|--------|-----------|
| Health | `/health` | readiness, liveness |
| Crypto | `/api/v1/crypto` | coins, prices, history |
| Economic | `/api/v1/economic` | indicators, GDP, inflation, rates |
| Analytics | `/api/v1/analytics` | BTC-inflation correlation, macro overview |
| **Monitor** | `/api/v1/monitor` | DAGs, runs, tasks, trigger, pause (Airflow proxy) |
| **Ingestion** | `/api/v1/ingestion` | sources, status, history, stats, overview |
| **Dashboard** | `/api/v1/dashboard` | KPIs, revenue-trends, top-products, segments, delivery, order-status |
| **Query** | `/api/v1/query/trino` | execute (SQL), schemas, tables, columns |

## Data Sources

### E-Commerce (Olist)
9 CSV tables → Bronze → dbt staging → intermediate → Gold marts:
- `mart_sales` / `mart_sales_monthly` — revenue, AOV, order volume
- `mart_customers` — RFM segmentation
- `mart_logistics` / `mart_logistics_by_state` — delivery KPIs
- `fct_orders` / `dim_customers` — fact + dimension tables

### Crypto (5 sources)
Binance (WebSocket), CoinGecko, CryptoCompare, Blockchain.info, Fear & Greed

### Economic (10+ sources)
FRED, BEA, BLS, Treasury, Census, World Bank, IMF, OECD, WTO, Penn World Tables

### Enterprise (MSSQL)
External SQL Server at `45.124.94.158:1433` (xomdata_dataset)

## Monitoring

| Dashboard | URL | Data |
|-----------|-----|------|
| Grafana — Pipeline Health | `http://localhost:3001/grafana/` | DAG runs, ingestion rates, dbt duration |
| Grafana — Data Freshness | `http://localhost:3001/grafana/` | Checkpoint ages, API rate limits |
| Grafana — Data Quality | `http://localhost:3001/grafana/` | GE validations, dbt test pass rate |
| Prometheus | `http://localhost:9090` | Raw metrics |
| FastAPI Metrics | `http://localhost:8000/metrics` | API + pipeline metrics |

### Alert Rules (10 rules)
- DAG failures, slow DAGs, ingestion errors, stale data
- GE validation failures, dbt test rate drops
- API latency/error rate, slow database/Trino queries

## Testing

```bash
make test              # All tests
make test-dags         # DAG integrity (syntax, imports, conventions)
make test-unit         # Unit tests
make quality-all       # Great Expectations (Olist + MSSQL suites)
make lint              # flake8 + isort + black --check
make type-check        # mypy
```

## Commands (Makefile)

```bash
make help              # Show all available commands
make docker-up         # Start infrastructure (Postgres, CH, Redis, Kafka, MinIO, monitoring)
make docker-up-full    # Start everything including API + Airflow
make api-dev           # FastAPI dev server (:8000)
make ui-dev            # Next.js dev server (:3000)
make dbt-run           # Run dbt models
make dbt-test          # Run dbt tests
make ingest-olist      # Olist CSV ingestion
make quality-all       # Great Expectations checks
make grafana-open      # Open Grafana in browser
```

## License

MIT License — see [LICENSE](LICENSE).
