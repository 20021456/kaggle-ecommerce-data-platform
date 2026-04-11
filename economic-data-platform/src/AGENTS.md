# src/ — Backend & Shared Library

## OVERVIEW

Two concerns: FastAPI REST API (`api/`) and installable shared Python library (`data_platform/`). Also contains Pydantic models (`models/`) and utility functions (`utils/`).

## STRUCTURE

```
src/
├── api/                    # FastAPI application
│   ├── main.py             # App factory, middleware, router registration
│   ├── config.py           # API-specific settings (host, port, CORS, rate limits)
│   └── routers/            # Domain routers (8 total)
│       ├── crypto.py       # Crypto market data (CoinGecko, Fear&Greed)
│       ├── economic.py     # FRED, BEA, BLS, Treasury, World Bank
│       ├── analytics.py    # Cross-domain: BTC-inflation, correlations
│       ├── health.py       # Health checks, readiness, liveness
│       ├── monitor.py      # [Phase 7] Airflow proxy (DAGs, runs, trigger)
│       ├── ingestion.py    # [Phase 7] Data source monitoring (status, history, stats)
│       ├── dashboard.py    # [Phase 7] E-commerce analytics (KPIs, revenue, RFM)
│       └── query.py        # [Phase 7] Ad-hoc Trino SQL (read-only)
├── data_platform/          # Shared library (pip install -e src/)
│   ├── common/             # logger, config (YAML), retry decorator, datetime_utils
│   ├── io/                 # Read/write abstractions (scaffolded)
│   ├── spark/              # Spark utilities (scaffolded)
│   ├── quality/            # Data quality helpers (scaffolded)
│   ├── alerting/           # Notification helpers (scaffolded)
│   └── models/             # Shared data models (scaffolded)
├── models/
│   └── schemas.py          # Pydantic models: EconomicDataRecord, CryptoPrice, MSSQLRecord
└── utils/
    ├── logger.py           # Structured logging (get_logger)
    ├── helpers.py           # General helpers
    ├── checkpoint_manager.py # Ingestion checkpoint tracking
    └── metrics.py           # Prometheus metrics (API_CALLS, RATE_LIMIT_REMAINING, etc.)
```

## WHERE TO LOOK

| Task | File |
|------|------|
| Add API route | `api/routers/` — create file, register in `api/main.py` line 200-208 |
| Modify API middleware | `api/main.py` — CORS (line 86), rate limit (line 124), request log (line 96) |
| Add Pydantic model | `models/schemas.py` |
| Add shared utility | `utils/` or `data_platform/common/` depending on scope |
| Prometheus metric | `utils/metrics.py` |

## CONVENTIONS

- API routers: `prefix="/api/v1/{domain}"`, `tags=["{Domain}"]`
- Prometheus metrics mounted at `/metrics` via `make_asgi_app()`
- `data_platform/` submodules mostly scaffolded (only `common/` has real code)
- `utils/logger.py` provides `get_logger(__name__)` — used everywhere
- API config in `api/config.py` separate from ingestion config

## ANTI-PATTERNS

- `data_platform/` has many empty `__init__.py`-only modules (io, spark, quality, alerting, models). Don't import from them expecting real code.
- Two separate config systems: `api/config.py` (API settings) vs `data_platform/common/config.py` (YAML loader) vs `ingestion/custom/config.py` (master Pydantic Settings). The ingestion config is the most complete.
