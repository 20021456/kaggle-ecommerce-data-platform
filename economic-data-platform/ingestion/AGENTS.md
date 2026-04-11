# ingestion/ — Data Source Connectors

## OVERVIEW

20+ API and database connectors for crypto, economic, and research data sources. Built on `BaseAPIClient` abstraction with rate limiting, retries, caching, and Prometheus metrics.

## STRUCTURE

```
ingestion/
├── custom/
│   ├── base_client.py      # BaseAPIClient (sync) + AsyncBaseAPIClient — THE base class
│   ├── base.py             # Alternative base (older)
│   ├── api_client.py       # Generic API client helper
│   ├── config.py           # ⭐ Master config: ALL env vars (Pydantic Settings)
│   ├── mssql_client.py     # MSSQL Server connector
│   ├── db_reader.py        # Generic DB reader
│   ├── db/
│   │   └── db_reader.py    # Database reader (nested version)
│   └── api/
│       ├── api_client.py   # Shared API helpers
│       ├── crypto/         # ✅ Canonical crypto connectors
│       │   ├── binance_websocket.py
│       │   ├── coingecko_client.py
│       │   ├── cryptocompare_client.py
│       │   ├── blockchain_client.py
│       │   └── fear_greed_client.py
│       ├── economic/       # ✅ Canonical economic connectors
│       │   ├── fred_client.py
│       │   ├── bea_client.py
│       │   ├── bls_client.py
│       │   ├── treasury_client.py
│       │   └── worldbank_client.py
│       ├── *.py            # ⚠️ Flat duplicates — use crypto/ and economic/ instead
│       └── __init__.py
└── schemas/                # Empty — JSON/Avro schemas would go here
```

## CONVENTIONS

- **New connector**: Create in `custom/api/{domain}/`, extend `BaseAPIClient` from `base_client.py`
- **Required methods**: `health_check() -> bool` and `get_source_name() -> str`
- **Rate limiting**: Set `rate_limit` param in constructor (requests/minute)
- **Config access**: `from ingestion.custom.config import settings` (or `from src.ingestion.config import settings` depending on PYTHONPATH)
- **Metrics**: `API_CALLS`, `RATE_LIMIT_REMAINING`, `INGESTION_DURATION` from `src.utils.metrics`

## ANTI-PATTERNS

- **Flat duplicate files**: `custom/api/fred_client.py` duplicates `custom/api/economic/fred_client.py`. Use the nested `crypto/` and `economic/` subdirectories.
- **Flat duplicate DB readers**: `custom/db_reader.py` duplicates `custom/db/db_reader.py`.
- **Hardcoded MSSQL creds**: `config.py` line 49-53 has default MSSQL host/user/password. Always override via `.env`.
- **Import path ambiguity**: `base_client.py` uses `from src.ingestion.config` but directory is `ingestion/custom/`. Ensure PYTHONPATH includes project root.
