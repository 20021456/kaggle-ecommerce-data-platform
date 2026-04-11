# ECONOMIC DATA PLATFORM

Multi-domain data analytics platform: crypto/financial + macroeconomic data. Medallion architecture (Bronze → Silver → Gold) with FastAPI serving layer and Next.js dashboard.

## STRUCTURE

```
economic-data-platform/
├── src/                  # Backend: FastAPI API + data_platform shared library
├── ingestion/            # 20+ data source connectors (API + DB)
├── airflow/              # Orchestration DAGs
├── dbt/                  # SQL transformation models (4 layers)
├── spark/                # Spark jobs (scaffolded)
├── ui/                   # Next.js frontend
├── infra/                # Docker, Terraform, K8s, CI/CD templates
├── dokploy/              # Production deployment (Dokploy PaaS)
├── sql/postgres/         # DDL: 01_bronze → 05_gold_combined
├── monitoring/           # Prometheus/Grafana configs
├── data_quality/         # GE + custom checks (scaffolded)
├── scripts/              # Deploy, backup, test scripts
└── tests/                # DAG + transform tests
```

## DATA FLOW

```
Sources (20+ APIs/DBs)
    ↓ ingestion/custom/api/ + ingestion/custom/db/
PostgreSQL Bronze (sql/01_bronze_schema.sql)
    ↓ spark/ jobs
PostgreSQL Silver (sql/02_silver_schema.sql)
    ↓ dbt/ models (staging → intermediate)
PostgreSQL/ClickHouse Gold (sql/03-05_gold_*.sql, dbt/models/marts/)
    ↓
FastAPI (src/api/) + Next.js (ui/)
    ↑ Orchestrated by Airflow (airflow/dags/)
```

## WHERE TO LOOK

| Task | Location |
|------|----------|
| New API endpoint | `src/api/routers/` — add router, register in `main.py` |
| New data source | `ingestion/custom/api/{domain}/` — extend `BaseAPIClient` |
| New dbt model | `dbt/models/{layer}/{domain}/` — follow `stg_`/`int_`/`fct_` naming |
| New Airflow DAG | `airflow/dags/{category}/` — import `DEFAULT_ARGS` |
| DB schema change | `sql/postgres/` — numbered migration files |
| Environment vars | `ingestion/custom/config.py` — single Pydantic Settings class |
| Deploy | `dokploy/` or `scripts/deploy.sh` |

## CONVENTIONS

- Restructured per `data_platform_standard.md` (see `RESTRUCTURE_SUMMARY.md`)
- `src/data_platform/` is an installable shared library: `pip install -e src/`
- All API clients inherit `BaseAPIClient` or `AsyncBaseAPIClient`
- dbt: 4 layers (sources → stagings → intermediate → marts), tests in `_*.yml` files
- Airflow: `common/default_args.py` for shared config, `common/callbacks.py` for alerts

## ANTI-PATTERNS

- `image/` directory is a stale Next.js app — use `ui/` instead
- Flat API client files in `ingestion/custom/api/` duplicate nested ones in `crypto/`/`economic/`
- `spark/` and `data_quality/` are scaffolded but empty — don't rely on them
- Default MSSQL credentials hardcoded in `config.py` — override via `.env`

## SERVICES (docker-compose.yml)

| Service | Port | Profile |
|---------|------|---------|
| PostgreSQL | 5432 | default |
| ClickHouse | 8123/9000 | default |
| Redis | 6379 | default |
| Kafka | 9092 | default |
| MinIO | 9000/9001 | default |
| Prometheus | 9090 | default |
| Grafana | 3000 | default |
| FastAPI | 8000 | `api` |
| Airflow Web | 8080 | `airflow` |
