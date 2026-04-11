# PROJECT KNOWLEDGE BASE

**Generated:** 2026-03-28
**Commit:** 8c07100
**Branch:** main

## OVERVIEW

Economic Data Analytics Platform — polyglot monorepo (Python 3.11 + TypeScript) implementing a medallion-architecture data pipeline. Ingests crypto/financial + macroeconomic data from 20+ APIs/databases, processes via Spark + dbt, serves via FastAPI + Next.js UI. Deployed with Dokploy (Docker PaaS).

## STRUCTURE

```
.
├── economic-data-platform/   # Main project (all code lives here)
│   ├── src/                  # Python backend: FastAPI API + shared data_platform library
│   ├── ingestion/            # Data ingestion clients (20+ API/DB connectors)
│   ├── airflow/              # Orchestration: DAGs, plugins, common args
│   ├── dbt/                  # SQL transformations: staging → intermediate → marts
│   ├── spark/                # Spark processing jobs (scaffolded, mostly empty)
│   ├── ui/                   # Next.js frontend dashboard
│   ├── image/                # Legacy/alternate Next.js app (screenshots + old UI)
│   ├── infra/                # IaC: Docker, Terraform, Kubernetes, CI/CD templates
│   ├── dokploy/              # Dokploy deployment configs (2 projects: DBs + app)
│   ├── sql/postgres/         # DDL: Bronze → Silver → Gold schema definitions
│   ├── monitoring/           # Prometheus + Grafana configs and dashboards
│   ├── data_quality/         # Great Expectations + custom checks (scaffolded)
│   ├── scripts/              # deploy.sh, backup.sh, test_mssql_connection.py
│   ├── tests/                # test_dags/, test_transform/
│   └── docs/                 # DOKPLOY_DEPLOYMENT.md
├── data_platform_standard.md # Architecture standard (Vietnamese) — THE governing doc
├── DEPLOYMENT_GUIDE.md       # Step-by-step deployment instructions
└── .sisyphus/                # AI orchestration metadata
```

## WHERE TO LOOK

| Task | Location | Notes |
|------|----------|-------|
| Add API endpoint | `economic-data-platform/src/api/routers/` | FastAPI routers: crypto, economic, analytics, health |
| Add data source connector | `economic-data-platform/ingestion/custom/api/` | Extend `BaseAPIClient` from `base_client.py` |
| Add/modify dbt model | `economic-data-platform/dbt/models/` | 4 layers: sources → stagings → intermediate → marts |
| Add Airflow DAG | `economic-data-platform/airflow/dags/` | Use `DEFAULT_ARGS` from `common/default_args.py` |
| Modify DB schema | `economic-data-platform/sql/postgres/` | Numbered files: 01_bronze → 05_gold_combined |
| Frontend work | `economic-data-platform/ui/` | Next.js + shadcn/ui + Tailwind |
| Deploy to production | `economic-data-platform/dokploy/` | Two Dokploy projects: shared-databases + application |
| Understand architecture | `data_platform_standard.md` | Vietnamese — canonical structure reference |
| Docker local dev | `economic-data-platform/docker-compose.yml` | Full stack: Postgres, ClickHouse, Redis, Kafka, MinIO |
| Pydantic schemas | `economic-data-platform/src/models/schemas.py` | EconomicDataRecord, CryptoPrice, MSSQLRecord |
| Shared Python utilities | `economic-data-platform/src/data_platform/common/` | logger, config, retry, datetime_utils |
| Environment config | `economic-data-platform/ingestion/custom/config.py` | Pydantic Settings — ALL env vars defined here |

## CONVENTIONS

- **Architecture standard**: `data_platform_standard.md` is the governing document. Project was restructured per this standard (see `RESTRUCTURE_SUMMARY.md`).
- **Python**: 3.11+, Poetry (root pyproject.toml) + setuptools (src/pyproject.toml for data_platform lib). Install shared lib with `pip install -e src/`.
- **Formatting**: Black, isort, flake8, mypy. Run via `make lint`, `make format`, `make type-check`.
- **Config**: Pydantic `BaseSettings` with `.env` file. ALL settings centralized in `ingestion/custom/config.py`.
- **API clients**: Inherit from `BaseAPIClient` (sync) or `AsyncBaseAPIClient` (async) in `ingestion/custom/base_client.py`. Provides rate limiting, retries, caching, metrics.
- **dbt naming**: `stg_` (staging/view), `int_` (intermediate/view), `fct_` (fact/table), `dim_` (dimension/table).
- **dbt materialization**: staging=view, intermediate=view, marts=table.
- **Airflow DAGs**: Use `DEFAULT_ARGS` from `airflow/common/default_args.py`. Owner: `data-team`.
- **Commit convention**: `<type>(<scope>): <subject>` — types: feat, fix, refactor, test, docs, chore, perf.
- **Branch strategy**: main → staging → develop → feature branches (`feat/`, `fix/`, `chore/`).

## ANTI-PATTERNS (THIS PROJECT)

- **Hardcoded credentials in config.py**: `ingestion/custom/config.py` has MSSQL default password in source code. Use env vars.
- **Duplicate connectors**: API clients exist at BOTH `ingestion/custom/api/*.py` (flat) AND `ingestion/custom/api/crypto/`, `ingestion/custom/api/economic/` (nested). The nested versions are canonical.
- **image/ vs ui/**: `image/` is an older/alternate Next.js app. `ui/` is the active frontend. Don't modify `image/`.
- **Empty scaffold dirs**: `spark/jobs/ingestion/`, `spark/jobs/transformation/`, `data_quality/great_expectations/`, `data_quality/custom_checks/`, `config/` are empty. Don't assume they contain working code.
- **Import paths inconsistency**: `base_client.py` imports from `src.ingestion.config` but lives in `ingestion/custom/`. Import paths may break depending on PYTHONPATH.
- **Two config systems**: `ingestion/custom/config.py` (Pydantic Settings) vs `src/data_platform/common/config.py` (YAML loader). They serve different purposes but overlap.

## COMMANDS

```bash
# Local dev
make docker-up              # Start full stack (Postgres, ClickHouse, Redis, Kafka, MinIO, monitoring)
make docker-down            # Stop all
make api-dev                # uvicorn src.api.main:app --reload

# Tests
make test                   # pytest tests/ -v --cov=src
make test-unit              # pytest tests/unit/
make test-int               # pytest tests/integration/

# Code quality
make lint                   # flake8 + isort + black --check
make format                 # isort + black
make type-check             # mypy src/

# dbt (from economic-data-platform/)
make dbt-run                # Run all models
make dbt-test               # Run dbt tests

# Data ingestion
make ingest-crypto          # python -m src.ingestion.crypto.run_ingestion
make ingest-econ            # python -m src.ingestion.economic.run_ingestion

# Deployment
bash scripts/deploy.sh      # Full production deploy
bash scripts/deploy-dokploy.sh  # Dokploy deploy
```

## NOTES

- **No CI pipeline** in repo. Build/test/lint are Makefile-driven only.
- **Vietnamese documentation**: `data_platform_standard.md` and `RESTRUCTURE_SUMMARY.md` are in Vietnamese.
- **MSSQL source**: External MSSQL server at `45.124.94.158:1433` (database: `xomdata_dataset`). Connection script at `scripts/test_mssql_connection.py`.
- **Docker profiles**: API and Airflow are behind `--profile api` and `--profile airflow` flags in docker-compose.yml. `make docker-up` starts infra only; use `make docker-up-full` for everything.
- **Prometheus metrics**: Mounted at `/metrics` on the FastAPI app via `prometheus_client.make_asgi_app()`.
