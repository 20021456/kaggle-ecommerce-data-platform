-- =============================================================================
-- SILVER LAYER — Cleaned & standardized (ReplacingMergeTree for dedup)
-- =============================================================================

-- Daily crypto prices (deduplicated by coin_id + price_date)
CREATE TABLE IF NOT EXISTS silver.crypto_prices_daily
(
    processed_at   DateTime64(3) DEFAULT now64(),
    coin_id        LowCardinality(String),
    symbol         LowCardinality(String),
    name           String,
    price_date     Date,
    open_price     Decimal128(10),
    high_price     Decimal128(10),
    low_price      Decimal128(10),
    close_price    Decimal128(10),
    volume_usd     Decimal128(2),
    market_cap_usd Decimal128(2),
    price_change_pct Decimal64(4),
    volatility     Decimal64(4),
    data_source    LowCardinality(String),
    is_imputed     UInt8 DEFAULT 0
)
ENGINE = ReplacingMergeTree(processed_at)
PARTITION BY toYYYYMM(price_date)
ORDER BY (coin_id, price_date)
SETTINGS index_granularity = 8192;

-- Hourly crypto prices
CREATE TABLE IF NOT EXISTS silver.crypto_prices_hourly
(
    processed_at   DateTime64(3) DEFAULT now64(),
    coin_id        LowCardinality(String),
    symbol         LowCardinality(String),
    price_hour     DateTime64(3),
    open_price     Decimal128(10),
    high_price     Decimal128(10),
    low_price      Decimal128(10),
    close_price    Decimal128(10),
    volume_usd     Decimal128(2),
    trades_count   UInt32,
    data_source    LowCardinality(String)
)
ENGINE = ReplacingMergeTree(processed_at)
PARTITION BY toYYYYMM(toDate(price_hour))
ORDER BY (coin_id, price_hour)
SETTINGS index_granularity = 8192;

-- Market sentiment
CREATE TABLE IF NOT EXISTS silver.market_sentiment
(
    processed_at             DateTime64(3) DEFAULT now64(),
    sentiment_date           Date,
    fear_greed_value         UInt8,
    fear_greed_classification LowCardinality(String),
    sentiment_score          Decimal64(4),
    fear_greed_ma7           Decimal64(2)
)
ENGINE = ReplacingMergeTree(processed_at)
PARTITION BY toYYYYMM(sentiment_date)
ORDER BY (sentiment_date)
SETTINGS index_granularity = 8192;

-- Economic indicators (FRED + others)
CREATE TABLE IF NOT EXISTS silver.economic_indicators
(
    processed_at     DateTime64(3) DEFAULT now64(),
    series_id        LowCardinality(String),
    indicator_name   String,
    observation_date Date,
    frequency        LowCardinality(String),
    value            Decimal128(10),
    units            LowCardinality(String),
    pct_change_mom   Nullable(Decimal64(4)),
    pct_change_yoy   Nullable(Decimal64(4)),
    is_preliminary   UInt8 DEFAULT 0,
    data_source      LowCardinality(String)
)
ENGINE = ReplacingMergeTree(processed_at)
PARTITION BY toYYYYMM(observation_date)
ORDER BY (series_id, observation_date)
SETTINGS index_granularity = 8192;

-- Treasury yields
CREATE TABLE IF NOT EXISTS silver.treasury_yields
(
    processed_at   DateTime64(3) DEFAULT now64(),
    record_date    Date,
    yield_1m       Nullable(Decimal64(4)),
    yield_3m       Nullable(Decimal64(4)),
    yield_6m       Nullable(Decimal64(4)),
    yield_1y       Nullable(Decimal64(4)),
    yield_2y       Nullable(Decimal64(4)),
    yield_3y       Nullable(Decimal64(4)),
    yield_5y       Nullable(Decimal64(4)),
    yield_7y       Nullable(Decimal64(4)),
    yield_10y      Nullable(Decimal64(4)),
    yield_20y      Nullable(Decimal64(4)),
    yield_30y      Nullable(Decimal64(4)),
    spread_10y_2y  Nullable(Decimal64(4)),
    spread_10y_3m  Nullable(Decimal64(4)),
    is_inverted    UInt8 DEFAULT 0
)
ENGINE = ReplacingMergeTree(processed_at)
PARTITION BY toYYYYMM(record_date)
ORDER BY (record_date)
SETTINGS index_granularity = 8192;
