-- =============================================================================
-- Minimal Database Schema for Small VPS
-- Economic Data Analytics Platform
-- =============================================================================
-- Combined schema - Bronze + Silver + Gold in one file
-- Optimized indexes for low memory
-- =============================================================================

-- Create schemas
CREATE SCHEMA IF NOT EXISTS bronze;
CREATE SCHEMA IF NOT EXISTS silver;
CREATE SCHEMA IF NOT EXISTS gold;

-- =============================================================================
-- BRONZE LAYER - Raw Data
-- =============================================================================

-- Crypto: CoinGecko prices
CREATE TABLE IF NOT EXISTS bronze.coingecko_prices (
    id SERIAL PRIMARY KEY,
    coin_id VARCHAR(100) NOT NULL,
    symbol VARCHAR(20),
    current_price DECIMAL(20, 8),
    market_cap DECIMAL(30, 2),
    total_volume DECIMAL(30, 2),
    price_change_24h DECIMAL(20, 8),
    price_change_percentage_24h DECIMAL(10, 4),
    raw_data JSONB,
    ingested_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Crypto: Fear & Greed Index
CREATE TABLE IF NOT EXISTS bronze.fear_greed_index (
    id SERIAL PRIMARY KEY,
    value INTEGER,
    classification VARCHAR(50),
    timestamp BIGINT,
    raw_data JSONB,
    ingested_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Economic: FRED observations
CREATE TABLE IF NOT EXISTS bronze.fred_observations (
    id SERIAL PRIMARY KEY,
    series_id VARCHAR(50) NOT NULL,
    observation_date DATE NOT NULL,
    value DECIMAL(20, 6),
    raw_data JSONB,
    ingested_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Economic: FRED series metadata
CREATE TABLE IF NOT EXISTS bronze.fred_series_metadata (
    id SERIAL PRIMARY KEY,
    series_id VARCHAR(50) NOT NULL UNIQUE,
    title TEXT,
    frequency VARCHAR(20),
    units VARCHAR(100),
    seasonal_adjustment VARCHAR(50),
    last_updated TIMESTAMP,
    raw_data JSONB,
    ingested_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Economic: World Bank indicators
CREATE TABLE IF NOT EXISTS bronze.worldbank_indicators (
    id SERIAL PRIMARY KEY,
    country_code VARCHAR(10),
    country_name VARCHAR(100),
    indicator_code VARCHAR(50),
    indicator_name TEXT,
    year INTEGER,
    value DECIMAL(20, 6),
    raw_data JSONB,
    ingested_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Economic: Treasury rates
CREATE TABLE IF NOT EXISTS bronze.treasury_rates (
    id SERIAL PRIMARY KEY,
    record_date DATE NOT NULL,
    security_type VARCHAR(50),
    security_desc VARCHAR(100),
    avg_interest_rate DECIMAL(10, 4),
    raw_data JSONB,
    ingested_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- =============================================================================
-- SILVER LAYER - Cleaned Data
-- =============================================================================

-- Crypto: Daily prices
CREATE TABLE IF NOT EXISTS silver.crypto_prices_daily (
    id SERIAL PRIMARY KEY,
    coin_id VARCHAR(100) NOT NULL,
    symbol VARCHAR(20),
    date DATE NOT NULL,
    open_price DECIMAL(20, 8),
    high_price DECIMAL(20, 8),
    low_price DECIMAL(20, 8),
    close_price DECIMAL(20, 8),
    volume DECIMAL(30, 2),
    market_cap DECIMAL(30, 2),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(coin_id, date)
);

-- Market sentiment
CREATE TABLE IF NOT EXISTS silver.market_sentiment (
    id SERIAL PRIMARY KEY,
    date DATE NOT NULL UNIQUE,
    fear_greed_value INTEGER,
    fear_greed_classification VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Economic indicators (cleaned)
CREATE TABLE IF NOT EXISTS silver.economic_indicators (
    id SERIAL PRIMARY KEY,
    series_id VARCHAR(50) NOT NULL,
    indicator_name VARCHAR(200),
    observation_date DATE NOT NULL,
    value DECIMAL(20, 6),
    unit VARCHAR(50),
    frequency VARCHAR(20),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(series_id, observation_date)
);

-- =============================================================================
-- GOLD LAYER - Analytics Ready
-- =============================================================================

-- Fact: Crypto-Macro daily (main analytics table)
CREATE TABLE IF NOT EXISTS gold.fct_crypto_macro_daily (
    id SERIAL PRIMARY KEY,
    observation_date DATE NOT NULL UNIQUE,
    
    -- Bitcoin
    btc_price DECIMAL(20, 2),
    btc_market_cap DECIMAL(30, 2),
    btc_volume DECIMAL(30, 2),
    btc_return_1d DECIMAL(10, 6),
    btc_return_7d DECIMAL(10, 6),
    btc_return_30d DECIMAL(10, 6),
    
    -- Sentiment
    fear_greed_value INTEGER,
    fear_greed_class VARCHAR(50),
    
    -- Macro indicators
    unemployment_rate DECIMAL(10, 4),
    cpi_value DECIMAL(10, 4),
    fed_funds_rate DECIMAL(10, 4),
    treasury_10y DECIMAL(10, 4),
    sp500_close DECIMAL(20, 2),
    gold_price DECIMAL(20, 2),
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- =============================================================================
-- INDEXES (Minimal - only essential)
-- =============================================================================

CREATE INDEX IF NOT EXISTS idx_bronze_coingecko_coin_date 
    ON bronze.coingecko_prices(coin_id, ingested_at);

CREATE INDEX IF NOT EXISTS idx_bronze_fred_series_date 
    ON bronze.fred_observations(series_id, observation_date);

CREATE INDEX IF NOT EXISTS idx_silver_crypto_coin_date 
    ON silver.crypto_prices_daily(coin_id, date);

CREATE INDEX IF NOT EXISTS idx_silver_econ_series_date 
    ON silver.economic_indicators(series_id, observation_date);

CREATE INDEX IF NOT EXISTS idx_gold_crypto_macro_date 
    ON gold.fct_crypto_macro_daily(observation_date);

-- =============================================================================
-- DONE
-- =============================================================================

SELECT 'Database initialized successfully!' as status;
