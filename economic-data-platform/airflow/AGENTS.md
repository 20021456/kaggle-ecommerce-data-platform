# airflow/ — Orchestration Layer

## OVERVIEW

Airflow DAGs organized by pipeline stage. Uses shared `DEFAULT_ARGS` and callbacks. LocalExecutor with PostgreSQL backend.

## STRUCTURE

```
airflow/
├── dags/
│   ├── ingestion/          # Data ingestion DAGs
│   │   └── etl_daily.py    # Daily ETL: extract → transform → load
│   ├── transformation/     # dbt / Spark transform DAGs
│   ├── export/             # Data export DAGs
│   └── maintenance/        # Cleanup / maintenance DAGs
├── common/
│   ├── default_args.py     # DEFAULT_ARGS: owner=data-team, retries=2, timeout=2h
│   └── callbacks.py        # on_failure / on_success callbacks
├── plugins/                # Custom operators, hooks, sensors
└── tests/                  # DAG integrity tests
```

## CONVENTIONS

- **Always** import `DEFAULT_ARGS` from `common.default_args` — don't redefine
- **DAG naming**: `{action}_{entity}` (e.g., `ingest_orders`, `transform_sales`)
- **DAG organization**: Place in correct subdirectory: `ingestion/`, `transformation/`, `export/`, `maintenance/`
- **Tags**: Include domain and stage tags (e.g., `['ingestion', 'crypto']`)
- DAGs are mounted to Airflow container via `./src/orchestration/dags` volume (see docker-compose)

## ANTI-PATTERNS

- `etl_daily.py` imports from `src.ingestion.db_reader` and `src.transform.cleaner` — these modules may not exist at those paths. Verify import paths match actual file locations.
- `etl_daily.py` uses old-style `DAG()` constructor instead of `@dag` decorator recommended in `data_platform_standard.md`.
