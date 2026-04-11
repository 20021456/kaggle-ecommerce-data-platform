-- =============================================================================
-- BRONZE LAYER — Raw ingestion tables (append-only, high throughput)
-- Engine: MergeTree with monthly partitioning + 90-day TTL
-- =============================================================================

-- Crypto prices from CoinGecko (batch ingestion)
CREATE TABLE IF NOT EXISTS bronze.coingecko_prices
(
    ingested_at    DateTime64(3) DEFAULT now64(),
    coin_id        LowCardinality(String),
    vs_currency    LowCardinality(String),
    timestamp_ms   Int64,
    price          Decimal128(10),
    market_cap     Decimal128(2),
    total_volume   Decimal128(2),
    raw_data       String  -- JSON blob
)
ENGINE = MergeTree()
PARTITION BY toYYYYMM(ingested_at)
ORDER BY (coin_id, timestamp_ms)
TTL toDateTime(ingested_at) + INTERVAL 180 DAY
SETTINGS index_granularity = 8192;

-- Binance trades (real-time via Kafka)
CREATE TABLE IF NOT EXISTS bronze.binance_trades
(
    ingested_at    DateTime64(3) DEFAULT now64(),
    trade_id       Int64,
    symbol         LowCardinality(String),
    price          Decimal128(10),
    quantity       Decimal128(10),
    trade_time     DateTime64(3),
    is_buyer_maker UInt8,
    raw_data       String
)
ENGINE = MergeTree()
PARTITION BY toYYYYMM(trade_time)
ORDER BY (symbol, trade_time, trade_id)
TTL toDateTime(trade_time) + INTERVAL 90 DAY
SETTINGS index_granularity = 8192;

-- Binance klines/candlesticks
CREATE TABLE IF NOT EXISTS bronze.binance_klines
(
    ingested_at  DateTime64(3) DEFAULT now64(),
    symbol       LowCardinality(String),
    interval     LowCardinality(String),
    open_time    DateTime64(3),
    close_time   DateTime64(3),
    open_price   Decimal128(10),
    high_price   Decimal128(10),
    low_price    Decimal128(10),
    close_price  Decimal128(10),
    volume       Decimal128(10),
    quote_volume Decimal128(10),
    trades_count UInt32,
    raw_data     String
)
ENGINE = MergeTree()
PARTITION BY toYYYYMM(open_time)
ORDER BY (symbol, interval, open_time)
TTL toDateTime(open_time) + INTERVAL 180 DAY
SETTINGS index_granularity = 8192;

-- Fear & Greed Index
CREATE TABLE IF NOT EXISTS bronze.fear_greed_index
(
    ingested_at    DateTime64(3) DEFAULT now64(),
    value_date     Date,
    value          UInt8,
    classification LowCardinality(String),
    timestamp_unix Int64,
    raw_data       String
)
ENGINE = MergeTree()
PARTITION BY toYYYYMM(value_date)
ORDER BY (value_date)
SETTINGS index_granularity = 8192;

-- FRED economic observations
CREATE TABLE IF NOT EXISTS bronze.fred_observations
(
    ingested_at      DateTime64(3) DEFAULT now64(),
    series_id        LowCardinality(String),
    observation_date Date,
    value            Nullable(Decimal128(10)),
    raw_data         String
)
ENGINE = MergeTree()
PARTITION BY toYYYYMM(observation_date)
ORDER BY (series_id, observation_date)
SETTINGS index_granularity = 8192;

-- World Bank indicators
CREATE TABLE IF NOT EXISTS bronze.worldbank_indicators
(
    ingested_at    DateTime64(3) DEFAULT now64(),
    country_id     LowCardinality(String),
    country_name   String,
    indicator_id   LowCardinality(String),
    indicator_name String,
    year           UInt16,
    value          Nullable(Decimal128(10)),
    raw_data       String
)
ENGINE = MergeTree()
PARTITION BY toYear(makeDate(year, 1, 1))
ORDER BY (country_id, indicator_id, year)
SETTINGS index_granularity = 8192;
