# dbt/ — SQL Transformation Layer

## OVERVIEW

dbt project implementing 4-layer medallion architecture. Profile: `economic_data_platform`. Targets PostgreSQL.

## STRUCTURE

```
dbt/
├── models/
│   ├── sources/            # Source definitions (sources.yml)
│   ├── stagings/           # Silver layer: cleaned, typed, validated
│   │   ├── crypto/         # stg_binance_trades, stg_coingecko_prices, incremental
│   │   └── economic/       # stg_fred_indicators, stg_worldbank_indicators
│   ├── intermediate/       # Processing: joins, aggregations, correlations
│   │   ├── crypto/         # int_crypto_daily_ohlcv
│   │   ├── economic/       # int_economic_indicators_pivoted
│   │   └── combined/       # int_btc_macro_correlation
│   └── marts/              # Gold: analytics-ready tables
│       ├── crypto/         # fct_crypto_daily_analytics
│       ├── economic/       # fct_economic_indicators
│       └── combined/       # fct_crypto_macro_analytics
├── macros/                 # data_platform_macros.sql
├── snapshots/              # coingecko_prices_snapshot (SCD Type 2)
├── seeds/                  # Static reference data
├── tests/                  # Custom data tests
├── dbt_project.yml         # Main config
└── profiles.yml            # Connection profiles
```

## CONVENTIONS

| Layer | Prefix | Materialization | Schema |
|-------|--------|-----------------|--------|
| Staging | `stg_` | view | `staging` |
| Intermediate | `int_` | view | `intermediate` |
| Marts (fact) | `fct_` | table | `gold_{domain}` |
| Marts (dim) | `dim_` | table | `gold_{domain}` |

- Tests and docs in `_{layer}.yml` files per directory
- Tags: `['crypto', 'staging']`, `['economic', 'intermediate']`, `['combined', 'mart']`
- Variables defined in `dbt_project.yml`: `start_date`, `top_crypto_ids`, `key_fred_series`, `major_economies`
- Default test severity: `warn`
- Snapshots use `timestamp` strategy with `updated_at` column
- **Note**: Directory is `stagings/` (plural) not `staging/` — deviation from standard

## ANTI-PATTERNS

- `models/staging/` directory exists alongside `models/stagings/` — only `stagings/` has content
- `models/sources/` exists but no `sources.yml` was found — may need creation

## COMMANDS

```bash
# From economic-data-platform/
make dbt-run        # cd src/processing/dbt_project && dbt run (⚠️ Makefile path differs from actual dbt/ location)
make dbt-test
make dbt-docs
```

**NOTE**: Makefile targets point to `src/processing/dbt_project` but dbt files are at `dbt/`. Adjust Makefile or use `cd dbt && dbt run` directly.
