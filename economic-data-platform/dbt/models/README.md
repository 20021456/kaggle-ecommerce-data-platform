# dbt Models Structure

## Layer 1: Sources (Bronze)
**Location:** `models/sources/`

Raw data definitions với schema và tests. Không transform data.

**Files:**
- `sources.yml` - Định nghĩa 20+ data sources (crypto + economic)

---

## Layer 2: Stagings (Silver)
**Location:** `models/stagings/`

Cleaned, typed, validated data. Chuẩn hóa naming conventions.

**Crypto:**
- `stg_binance_trades.sql` - Binance trades cleaned
- `stg_binance_trades_incremental.sql` - Incremental loading với CDC
- `stg_coingecko_prices.sql` - CoinGecko prices cleaned
- `_crypto_stagings.yml` - Tests và documentation

**Economic:**
- `stg_fred_indicators.sql` - FRED indicators cleaned
- `stg_worldbank_indicators.sql` - World Bank data cleaned
- `_economic_stagings.yml` - Tests và documentation

---

## Layer 3: Intermediate (Processing)
**Location:** `models/intermediate/`

Business logic transformations, aggregations, joins.

**Crypto:**
- `int_crypto_daily_ohlcv.sql` - Daily OHLCV aggregates với technical indicators

**Economic:**
- `int_economic_indicators_pivoted.sql` - Pivoted economic indicators với YoY calculations

**Combined:**
- `int_btc_macro_correlation.sql` - Bitcoin + macroeconomic correlations

**Documentation:**
- `_intermediate.yml` - Tests và schema definitions

---

## Layer 4: Marts (Gold)
**Location:** `models/marts/`

Final analytics tables for consumption.

**Crypto:**
- `fct_crypto_daily_analytics.sql` - Daily crypto analytics với signals (MA, volatility, trends)

**Economic:**
- `fct_economic_indicators.sql` - Economic indicators với regime classifications

**Combined:**
- `fct_crypto_macro_analytics.sql` - Cross-domain analytics (BTC vs inflation, rates, M2)

**Documentation:**
- `_marts.yml` - Tests và schema definitions

---

## Key Differences from Before

| Aspect | Before | After |
|--------|--------|-------|
| **Structure** | Flat, no layers | 4 layers: sources → stagings → intermediate → marts |
| **Tests** | None | 50+ tests in .yml files |
| **Incremental** | None | CDC logic với checkpoints |
| **Documentation** | Minimal | Column-level docs, tests, descriptions |
| **Cross-domain** | None | BTC-macro correlation models |
