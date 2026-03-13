-- =============================================================================
-- BRONZE SCHEMA - Raw Data Layer
-- Economic Data Analytics Platform
-- =============================================================================
-- This schema stores raw data exactly as received from source systems.
-- Data is immutable and append-only.
-- =============================================================================

-- Create Bronze Schema
CREATE SCHEMA IF NOT EXISTS bronze;

-- Set default schema
SET search_path TO bronze, public;

-- =============================================================================
-- CRYPTO DATA TABLES
-- =============================================================================

-- CoinGecko market data
CREATE TABLE IF NOT EXISTS bronze.coingecko_markets (
    id BIGSERIAL PRIMARY KEY,
    ingested_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    source_timestamp TIMESTAMP WITH TIME ZONE,
    raw_data JSONB NOT NULL,
    
    -- Extracted fields for querying
    coin_id VARCHAR(100),
    symbol VARCHAR(20),
    name VARCHAR(200),
    current_price DECIMAL(30, 10),
    market_cap DECIMAL(30, 2),
    total_volume DECIMAL(30, 2),
    price_change_24h DECIMAL(30, 10),
    price_change_percentage_24h DECIMAL(10, 4)
);

-- CoinGecko historical prices
CREATE TABLE IF NOT EXISTS bronze.coingecko_prices (
    id BIGSERIAL PRIMARY KEY,
    ingested_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    coin_id VARCHAR(100) NOT NULL,
    vs_currency VARCHAR(10) NOT NULL,
    timestamp_ms BIGINT NOT NULL,
    price DECIMAL(30, 10),
    market_cap DECIMAL(30, 2),
    total_volume DECIMAL(30, 2),
    raw_data JSONB
);

-- Binance trades (for streaming data)
CREATE TABLE IF NOT EXISTS bronze.binance_trades (
    id BIGSERIAL PRIMARY KEY,
    ingested_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    trade_id BIGINT,
    symbol VARCHAR(20) NOT NULL,
    price DECIMAL(30, 10) NOT NULL,
    quantity DECIMAL(30, 10) NOT NULL,
    trade_time TIMESTAMP WITH TIME ZONE,
    is_buyer_maker BOOLEAN,
    raw_data JSONB
);

-- Binance klines/candlesticks
CREATE TABLE IF NOT EXISTS bronze.binance_klines (
    id BIGSERIAL PRIMARY KEY,
    ingested_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    symbol VARCHAR(20) NOT NULL,
    interval VARCHAR(10) NOT NULL,
    open_time TIMESTAMP WITH TIME ZONE NOT NULL,
    close_time TIMESTAMP WITH TIME ZONE,
    open_price DECIMAL(30, 10),
    high_price DECIMAL(30, 10),
    low_price DECIMAL(30, 10),
    close_price DECIMAL(30, 10),
    volume DECIMAL(30, 10),
    quote_volume DECIMAL(30, 10),
    trades_count INTEGER,
    raw_data JSONB
);

-- CryptoCompare OHLCV
CREATE TABLE IF NOT EXISTS bronze.cryptocompare_ohlcv (
    id BIGSERIAL PRIMARY KEY,
    ingested_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    symbol VARCHAR(20) NOT NULL,
    vs_currency VARCHAR(10) NOT NULL,
    period VARCHAR(10) NOT NULL,  -- 'minute', 'hour', 'day'
    timestamp_unix BIGINT NOT NULL,
    open_price DECIMAL(30, 10),
    high_price DECIMAL(30, 10),
    low_price DECIMAL(30, 10),
    close_price DECIMAL(30, 10),
    volume_from DECIMAL(30, 10),
    volume_to DECIMAL(30, 10),
    raw_data JSONB
);

-- Blockchain.info Bitcoin data
CREATE TABLE IF NOT EXISTS bronze.blockchain_stats (
    id BIGSERIAL PRIMARY KEY,
    ingested_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    stat_date DATE,
    hash_rate DECIMAL(30, 2),
    difficulty DECIMAL(30, 2),
    total_btc DECIMAL(30, 8),
    block_height BIGINT,
    transactions_24h BIGINT,
    mempool_size BIGINT,
    price_usd DECIMAL(30, 2),
    raw_data JSONB
);

-- Fear & Greed Index
CREATE TABLE IF NOT EXISTS bronze.fear_greed_index (
    id BIGSERIAL PRIMARY KEY,
    ingested_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    value_date DATE NOT NULL,
    value INTEGER NOT NULL,
    classification VARCHAR(50),
    timestamp_unix BIGINT,
    raw_data JSONB
);

-- =============================================================================
-- ECONOMIC DATA TABLES
-- =============================================================================

-- FRED time series data
CREATE TABLE IF NOT EXISTS bronze.fred_observations (
    id BIGSERIAL PRIMARY KEY,
    ingested_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    series_id VARCHAR(50) NOT NULL,
    observation_date DATE NOT NULL,
    value DECIMAL(30, 10),
    raw_data JSONB
);

-- FRED series metadata
CREATE TABLE IF NOT EXISTS bronze.fred_series_metadata (
    id BIGSERIAL PRIMARY KEY,
    ingested_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    series_id VARCHAR(50) NOT NULL UNIQUE,
    title VARCHAR(500),
    observation_start DATE,
    observation_end DATE,
    frequency VARCHAR(50),
    units VARCHAR(200),
    seasonal_adjustment VARCHAR(200),
    notes TEXT,
    raw_data JSONB
);

-- BEA NIPA data
CREATE TABLE IF NOT EXISTS bronze.bea_nipa (
    id BIGSERIAL PRIMARY KEY,
    ingested_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    table_name VARCHAR(20) NOT NULL,
    series_code VARCHAR(50),
    line_number VARCHAR(20),
    line_description VARCHAR(500),
    time_period VARCHAR(20) NOT NULL,
    value DECIMAL(30, 10),
    raw_data JSONB
);

-- World Bank indicators
CREATE TABLE IF NOT EXISTS bronze.worldbank_indicators (
    id BIGSERIAL PRIMARY KEY,
    ingested_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    country_id VARCHAR(10) NOT NULL,
    country_name VARCHAR(200),
    indicator_id VARCHAR(50) NOT NULL,
    indicator_name VARCHAR(500),
    year INTEGER NOT NULL,
    value DECIMAL(30, 10),
    raw_data JSONB
);

-- Treasury interest rates
CREATE TABLE IF NOT EXISTS bronze.treasury_rates (
    id BIGSERIAL PRIMARY KEY,
    ingested_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    record_date DATE NOT NULL,
    security_type VARCHAR(100),
    security_desc VARCHAR(200),
    avg_interest_rate DECIMAL(10, 4),
    raw_data JSONB
);

-- Treasury debt statistics
CREATE TABLE IF NOT EXISTS bronze.treasury_debt (
    id BIGSERIAL PRIMARY KEY,
    ingested_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    record_date DATE NOT NULL,
    total_public_debt DECIMAL(30, 2),
    intragovernmental_holdings DECIMAL(30, 2),
    debt_held_by_public DECIMAL(30, 2),
    raw_data JSONB
);

-- BLS employment/CPI data
CREATE TABLE IF NOT EXISTS bronze.bls_observations (
    id BIGSERIAL PRIMARY KEY,
    ingested_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    series_id VARCHAR(50) NOT NULL,
    year INTEGER NOT NULL,
    period VARCHAR(10) NOT NULL,
    period_name VARCHAR(50),
    value DECIMAL(30, 10),
    pct_change_1m DECIMAL(10, 4),
    pct_change_12m DECIMAL(10, 4),
    raw_data JSONB
);

-- =============================================================================
-- RESEARCH DATA TABLES
-- =============================================================================

-- AEA ICPSR datasets metadata
CREATE TABLE IF NOT EXISTS bronze.aea_datasets (
    id BIGSERIAL PRIMARY KEY,
    ingested_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    dataset_id VARCHAR(100) NOT NULL,
    title VARCHAR(500),
    authors TEXT,
    publication_date DATE,
    doi VARCHAR(200),
    abstract TEXT,
    keywords TEXT[],
    raw_data JSONB
);

-- Generic research data storage
CREATE TABLE IF NOT EXISTS bronze.research_data (
    id BIGSERIAL PRIMARY KEY,
    ingested_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    source VARCHAR(100) NOT NULL,
    dataset_id VARCHAR(100) NOT NULL,
    record_data JSONB NOT NULL
);

-- =============================================================================
-- INDEXES FOR QUERY PERFORMANCE
-- =============================================================================

-- Crypto indexes
CREATE INDEX IF NOT EXISTS idx_coingecko_markets_coin_id ON bronze.coingecko_markets(coin_id);
CREATE INDEX IF NOT EXISTS idx_coingecko_markets_ingested ON bronze.coingecko_markets(ingested_at);
CREATE INDEX IF NOT EXISTS idx_coingecko_prices_coin_ts ON bronze.coingecko_prices(coin_id, timestamp_ms);
CREATE INDEX IF NOT EXISTS idx_binance_trades_symbol_time ON bronze.binance_trades(symbol, trade_time);
CREATE INDEX IF NOT EXISTS idx_binance_klines_symbol_time ON bronze.binance_klines(symbol, interval, open_time);
CREATE INDEX IF NOT EXISTS idx_cryptocompare_symbol_ts ON bronze.cryptocompare_ohlcv(symbol, timestamp_unix);
CREATE INDEX IF NOT EXISTS idx_fear_greed_date ON bronze.fear_greed_index(value_date);

-- Economic indexes
CREATE INDEX IF NOT EXISTS idx_fred_series_date ON bronze.fred_observations(series_id, observation_date);
CREATE INDEX IF NOT EXISTS idx_bea_table_period ON bronze.bea_nipa(table_name, time_period);
CREATE INDEX IF NOT EXISTS idx_worldbank_country_ind ON bronze.worldbank_indicators(country_id, indicator_id, year);
CREATE INDEX IF NOT EXISTS idx_treasury_rates_date ON bronze.treasury_rates(record_date);
CREATE INDEX IF NOT EXISTS idx_treasury_debt_date ON bronze.treasury_debt(record_date);
CREATE INDEX IF NOT EXISTS idx_bls_series_period ON bronze.bls_observations(series_id, year, period);

-- =============================================================================
-- COMMENTS FOR DOCUMENTATION
-- =============================================================================

COMMENT ON SCHEMA bronze IS 'Raw data layer - stores data exactly as received from sources';

COMMENT ON TABLE bronze.coingecko_markets IS 'Raw market data from CoinGecko API';
COMMENT ON TABLE bronze.binance_trades IS 'Raw trade data from Binance WebSocket';
COMMENT ON TABLE bronze.fred_observations IS 'Raw time series data from FRED API';
COMMENT ON TABLE bronze.worldbank_indicators IS 'Raw indicator data from World Bank API';
