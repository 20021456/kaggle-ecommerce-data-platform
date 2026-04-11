-- =============================================================================
-- KAFKA → ClickHouse Ingestion Pipeline
-- Uses Kafka engine tables + Materialized Views for real-time streaming
-- =============================================================================
-- Pattern: Kafka Engine (consumer) → Materialized View (transform) → MergeTree (storage)
-- =============================================================================

-- ─── BINANCE TRADES (real-time) ──────────────────────────────────────────────

-- Step 1: Kafka consumer table (reads from Kafka topic)
CREATE TABLE IF NOT EXISTS bronze._kafka_binance_trades
(
    trade_id       Int64,
    symbol         String,
    price          String,
    quantity       String,
    trade_time     Int64,
    is_buyer_maker UInt8,
    raw_data       String
)
ENGINE = Kafka()
SETTINGS
    kafka_broker_list = 'kafka:29092',
    kafka_topic_list = 'binance.trades',
    kafka_group_name = 'clickhouse_binance_trades',
    kafka_format = 'JSONEachRow',
    kafka_num_consumers = 2,
    kafka_max_block_size = 65536,
    kafka_flush_interval_ms = 1000;

-- Step 2: Materialized view (auto-inserts into target table on each Kafka batch)
CREATE MATERIALIZED VIEW IF NOT EXISTS bronze.mv_binance_trades
TO bronze.binance_trades AS
SELECT
    now64() AS ingested_at,
    trade_id,
    symbol,
    toDecimal128(price, 10) AS price,
    toDecimal128(quantity, 10) AS quantity,
    fromUnixTimestamp64Milli(trade_time) AS trade_time,
    is_buyer_maker,
    raw_data
FROM bronze._kafka_binance_trades;

-- ─── CRYPTO PRICES (batch from API, via Kafka for reliability) ───────────────

CREATE TABLE IF NOT EXISTS bronze._kafka_crypto_prices
(
    coin_id      String,
    vs_currency  String,
    timestamp_ms Int64,
    price        String,
    market_cap   String,
    total_volume String
)
ENGINE = Kafka()
SETTINGS
    kafka_broker_list = 'kafka:29092',
    kafka_topic_list = 'crypto.prices',
    kafka_group_name = 'clickhouse_crypto_prices',
    kafka_format = 'JSONEachRow',
    kafka_num_consumers = 1,
    kafka_max_block_size = 16384,
    kafka_flush_interval_ms = 5000;

CREATE MATERIALIZED VIEW IF NOT EXISTS bronze.mv_crypto_prices
TO bronze.coingecko_prices AS
SELECT
    now64() AS ingested_at,
    coin_id,
    vs_currency,
    timestamp_ms,
    toDecimal128(price, 10) AS price,
    toDecimal128(market_cap, 2) AS market_cap,
    toDecimal128(total_volume, 2) AS total_volume,
    '' AS raw_data
FROM bronze._kafka_crypto_prices;

-- ─── FEAR & GREED INDEX ──────────────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS bronze._kafka_fear_greed
(
    value_date     String,
    value          UInt8,
    classification String,
    timestamp_unix Int64
)
ENGINE = Kafka()
SETTINGS
    kafka_broker_list = 'kafka:29092',
    kafka_topic_list = 'crypto.fear_greed',
    kafka_group_name = 'clickhouse_fear_greed',
    kafka_format = 'JSONEachRow',
    kafka_num_consumers = 1,
    kafka_max_block_size = 1024,
    kafka_flush_interval_ms = 10000;

CREATE MATERIALIZED VIEW IF NOT EXISTS bronze.mv_fear_greed
TO bronze.fear_greed_index AS
SELECT
    now64() AS ingested_at,
    toDate(value_date) AS value_date,
    value,
    classification,
    timestamp_unix,
    '' AS raw_data
FROM bronze._kafka_fear_greed;

-- ─── ECONOMIC DATA (FRED) ────────────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS bronze._kafka_fred_observations
(
    series_id        String,
    observation_date String,
    value            Nullable(String)
)
ENGINE = Kafka()
SETTINGS
    kafka_broker_list = 'kafka:29092',
    kafka_topic_list = 'economic.fred',
    kafka_group_name = 'clickhouse_fred',
    kafka_format = 'JSONEachRow',
    kafka_num_consumers = 1,
    kafka_max_block_size = 8192,
    kafka_flush_interval_ms = 10000;

CREATE MATERIALIZED VIEW IF NOT EXISTS bronze.mv_fred_observations
TO bronze.fred_observations AS
SELECT
    now64() AS ingested_at,
    series_id,
    toDate(observation_date) AS observation_date,
    if(value IS NOT NULL AND value != '.', toDecimal128(value, 10), NULL) AS value,
    '' AS raw_data
FROM bronze._kafka_fred_observations;
