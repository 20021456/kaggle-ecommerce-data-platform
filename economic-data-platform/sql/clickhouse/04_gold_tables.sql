-- =============================================================================
-- GOLD LAYER — Analytics-ready tables for Grafana dashboards
-- Engine: MergeTree (fast reads) or AggregatingMergeTree (pre-aggregated)
-- =============================================================================

-- ─── CRYPTO ANALYTICS ────────────────────────────────────────────────────────

-- Daily crypto with technical indicators (main dashboard table)
CREATE TABLE IF NOT EXISTS gold.fct_crypto_daily
(
    coin_id          LowCardinality(String),
    price_date       Date,
    open_price       Decimal128(10),
    high_price       Decimal128(10),
    low_price        Decimal128(10),
    close_price      Decimal128(10),
    volume_usd       Decimal128(2),
    market_cap_usd   Decimal128(2),
    daily_return_pct Decimal64(6),
    daily_range_pct  Decimal64(4),
    sma_7d           Decimal128(10),
    sma_30d          Decimal128(10),
    sma_50d          Decimal128(10),
    sma_200d         Decimal128(10),
    volatility_7d    Decimal64(6),
    volatility_30d   Decimal64(6),
    rsi_14d          Decimal64(2),
    is_above_sma_50  UInt8,
    is_above_sma_200 UInt8,
    golden_cross     UInt8,
    death_cross      UInt8,
    volume_sma_20d   Decimal128(2),
    is_high_volume   UInt8
)
ENGINE = ReplacingMergeTree()
PARTITION BY toYYYYMM(price_date)
ORDER BY (coin_id, price_date)
SETTINGS index_granularity = 8192;

-- Hourly crypto for real-time dashboards
CREATE TABLE IF NOT EXISTS gold.fct_crypto_hourly
(
    coin_id          LowCardinality(String),
    price_hour       DateTime64(3),
    open_price       Decimal128(10),
    high_price       Decimal128(10),
    low_price        Decimal128(10),
    close_price      Decimal128(10),
    volume_usd       Decimal128(2),
    trades_count     UInt32,
    hourly_return_pct Decimal64(6),
    vwap             Decimal128(10),
    ema_12h          Decimal128(10),
    ema_24h          Decimal128(10)
)
ENGINE = ReplacingMergeTree()
PARTITION BY toYYYYMM(toDate(price_hour))
ORDER BY (coin_id, price_hour)
TTL toDateTime(price_hour) + INTERVAL 90 DAY
SETTINGS index_granularity = 8192;

-- ─── ECONOMIC ANALYTICS ──────────────────────────────────────────────────────

-- US economic indicators (wide table for dashboards)
CREATE TABLE IF NOT EXISTS gold.fct_us_indicators
(
    observation_date          Date,
    gdp_billions              Nullable(Decimal128(2)),
    gdp_growth_qoq           Nullable(Decimal64(3)),
    gdp_growth_yoy           Nullable(Decimal64(3)),
    unemployment_rate         Nullable(Decimal64(3)),
    nonfarm_payrolls_thousands Nullable(Int64),
    cpi_yoy                   Nullable(Decimal64(3)),
    core_cpi_yoy              Nullable(Decimal64(3)),
    pce_yoy                   Nullable(Decimal64(3)),
    fed_funds_rate            Nullable(Decimal64(4)),
    treasury_10y              Nullable(Decimal64(4)),
    treasury_2y               Nullable(Decimal64(4)),
    yield_curve_spread        Nullable(Decimal64(4)),
    m2_billions               Nullable(Decimal128(2)),
    m2_growth_yoy             Nullable(Decimal64(3)),
    consumer_sentiment        Nullable(Decimal64(2)),
    housing_starts_thousands  Nullable(Int32),
    mortgage_rate_30y         Nullable(Decimal64(4)),
    trade_balance_billions    Nullable(Decimal128(2))
)
ENGINE = ReplacingMergeTree()
PARTITION BY toYYYYMM(observation_date)
ORDER BY (observation_date)
SETTINGS index_granularity = 8192;

-- Treasury yield curve
CREATE TABLE IF NOT EXISTS gold.fct_yield_curve
(
    curve_date       Date,
    yield_1m         Nullable(Decimal64(4)),
    yield_3m         Nullable(Decimal64(4)),
    yield_6m         Nullable(Decimal64(4)),
    yield_1y         Nullable(Decimal64(4)),
    yield_2y         Nullable(Decimal64(4)),
    yield_3y         Nullable(Decimal64(4)),
    yield_5y         Nullable(Decimal64(4)),
    yield_7y         Nullable(Decimal64(4)),
    yield_10y        Nullable(Decimal64(4)),
    yield_20y        Nullable(Decimal64(4)),
    yield_30y        Nullable(Decimal64(4)),
    spread_2y_3m     Nullable(Decimal64(4)),
    spread_10y_2y    Nullable(Decimal64(4)),
    spread_10y_3m    Nullable(Decimal64(4)),
    spread_30y_10y   Nullable(Decimal64(4)),
    is_inverted      UInt8,
    inversion_depth  Nullable(Decimal64(4))
)
ENGINE = ReplacingMergeTree()
PARTITION BY toYYYYMM(curve_date)
ORDER BY (curve_date)
SETTINGS index_granularity = 8192;

-- ─── CROSS-DOMAIN ANALYTICS ──────────────────────────────────────────────────

-- Daily crypto + macro context (main Grafana dashboard)
CREATE TABLE IF NOT EXISTS gold.fct_crypto_macro_daily
(
    observation_date          Date,
    btc_price_usd             Decimal128(10),
    btc_return_daily_pct      Decimal64(6),
    btc_volatility_30d        Decimal64(6),
    btc_volume_usd            Decimal128(2),
    fear_greed_value          UInt8,
    fear_greed_classification LowCardinality(String),
    unemployment_rate         Nullable(Decimal64(3)),
    cpi_yoy                   Nullable(Decimal64(3)),
    fed_funds_rate            Nullable(Decimal64(4)),
    treasury_10y              Nullable(Decimal64(4)),
    yield_curve_spread        Nullable(Decimal64(4)),
    sp500_close               Nullable(Decimal128(2)),
    gold_price_usd            Nullable(Decimal128(2)),
    dxy_index                 Nullable(Decimal64(4)),
    m2_billions               Nullable(Decimal128(2)),
    btc_sp500_corr_30d        Nullable(Decimal64(4)),
    btc_gold_corr_30d         Nullable(Decimal64(4)),
    btc_dxy_corr_30d          Nullable(Decimal64(4))
)
ENGINE = ReplacingMergeTree()
PARTITION BY toYYYYMM(observation_date)
ORDER BY (observation_date)
SETTINGS index_granularity = 8192;

-- Market regime classification
CREATE TABLE IF NOT EXISTS gold.analysis_market_regime
(
    regime_date         Date,
    economic_cycle      LowCardinality(String),
    gdp_growth_trend    LowCardinality(String),
    inflation_regime    LowCardinality(String),
    fed_stance          LowCardinality(String),
    liquidity_conditions LowCardinality(String),
    risk_appetite       LowCardinality(String),
    volatility_regime   LowCardinality(String),
    crypto_market_phase LowCardinality(String),
    btc_trend           LowCardinality(String),
    risk_score          Decimal64(2),
    opportunity_score   Decimal64(2)
)
ENGINE = ReplacingMergeTree()
PARTITION BY toYYYYMM(regime_date)
ORDER BY (regime_date)
SETTINGS index_granularity = 8192;
