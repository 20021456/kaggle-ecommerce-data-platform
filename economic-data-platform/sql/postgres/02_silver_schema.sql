-- =============================================================================
-- SILVER SCHEMA - Cleaned & Standardized Data Layer
-- Economic Data Analytics Platform
-- =============================================================================
-- This schema stores cleaned, validated, and standardized data.
-- Data quality issues are resolved and formats are normalized.
-- =============================================================================

-- Create Silver Schema
CREATE SCHEMA IF NOT EXISTS silver;

-- Set default schema
SET search_path TO silver, public;

-- =============================================================================
-- CRYPTO DATA TABLES (CLEANED)
-- =============================================================================

-- Cleaned cryptocurrency prices (daily)
CREATE TABLE IF NOT EXISTS silver.crypto_prices_daily (
    id BIGSERIAL PRIMARY KEY,
    processed_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- Identification
    coin_id VARCHAR(100) NOT NULL,
    symbol VARCHAR(20) NOT NULL,
    name VARCHAR(200),
    
    -- Time
    price_date DATE NOT NULL,
    
    -- Price Data (in USD)
    open_price DECIMAL(30, 10),
    high_price DECIMAL(30, 10),
    low_price DECIMAL(30, 10),
    close_price DECIMAL(30, 10),
    
    -- Volume & Market Cap
    volume_usd DECIMAL(30, 2),
    market_cap_usd DECIMAL(30, 2),
    
    -- Calculated fields
    price_change_pct DECIMAL(10, 4),
    volatility DECIMAL(10, 4),
    
    -- Data quality
    data_source VARCHAR(50),
    is_imputed BOOLEAN DEFAULT FALSE,
    
    CONSTRAINT uq_crypto_price_daily UNIQUE (coin_id, price_date)
);

-- Cleaned cryptocurrency prices (hourly)
CREATE TABLE IF NOT EXISTS silver.crypto_prices_hourly (
    id BIGSERIAL PRIMARY KEY,
    processed_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    coin_id VARCHAR(100) NOT NULL,
    symbol VARCHAR(20) NOT NULL,
    price_hour TIMESTAMP WITH TIME ZONE NOT NULL,
    
    open_price DECIMAL(30, 10),
    high_price DECIMAL(30, 10),
    low_price DECIMAL(30, 10),
    close_price DECIMAL(30, 10),
    volume_usd DECIMAL(30, 2),
    trades_count INTEGER,
    
    data_source VARCHAR(50),
    
    CONSTRAINT uq_crypto_price_hourly UNIQUE (coin_id, price_hour)
);

-- Cleaned coin metadata
CREATE TABLE IF NOT EXISTS silver.crypto_coins (
    id BIGSERIAL PRIMARY KEY,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    coin_id VARCHAR(100) NOT NULL UNIQUE,
    symbol VARCHAR(20) NOT NULL,
    name VARCHAR(200) NOT NULL,
    
    -- Metadata
    description TEXT,
    website_url VARCHAR(500),
    github_url VARCHAR(500),
    twitter_handle VARCHAR(100),
    
    -- Classification
    category VARCHAR(100),
    genesis_date DATE,
    
    -- Current stats (denormalized for convenience)
    current_price_usd DECIMAL(30, 10),
    market_cap_usd DECIMAL(30, 2),
    market_cap_rank INTEGER,
    circulating_supply DECIMAL(30, 2),
    total_supply DECIMAL(30, 2),
    max_supply DECIMAL(30, 2),
    
    -- Status
    is_active BOOLEAN DEFAULT TRUE
);

-- Market sentiment (Fear & Greed)
CREATE TABLE IF NOT EXISTS silver.market_sentiment (
    id BIGSERIAL PRIMARY KEY,
    processed_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    sentiment_date DATE NOT NULL UNIQUE,
    fear_greed_value INTEGER NOT NULL CHECK (fear_greed_value BETWEEN 0 AND 100),
    fear_greed_classification VARCHAR(50),
    
    -- Normalized score (-1 to 1)
    sentiment_score DECIMAL(5, 4),
    
    -- 7-day moving average
    fear_greed_ma7 DECIMAL(10, 2)
);

-- Bitcoin network stats
CREATE TABLE IF NOT EXISTS silver.bitcoin_network_stats (
    id BIGSERIAL PRIMARY KEY,
    processed_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    stat_date DATE NOT NULL UNIQUE,
    
    hash_rate_eh DECIMAL(20, 2),  -- Exahash/s
    difficulty DECIMAL(30, 2),
    block_height BIGINT,
    
    total_btc_mined DECIMAL(20, 8),
    btc_mined_daily DECIMAL(20, 8),
    
    transactions_daily BIGINT,
    avg_block_time_seconds DECIMAL(10, 2),
    mempool_size_mb DECIMAL(10, 2),
    
    miners_revenue_usd DECIMAL(20, 2),
    transaction_fees_btc DECIMAL(20, 8)
);

-- =============================================================================
-- ECONOMIC DATA TABLES (CLEANED)
-- =============================================================================

-- Cleaned FRED economic indicators
CREATE TABLE IF NOT EXISTS silver.economic_indicators (
    id BIGSERIAL PRIMARY KEY,
    processed_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- Identification
    series_id VARCHAR(50) NOT NULL,
    indicator_name VARCHAR(500),
    
    -- Time
    observation_date DATE NOT NULL,
    frequency VARCHAR(20),  -- 'daily', 'monthly', 'quarterly', 'annual'
    
    -- Value
    value DECIMAL(30, 10) NOT NULL,
    units VARCHAR(200),
    
    -- Calculated fields
    pct_change_mom DECIMAL(10, 4),  -- Month over month
    pct_change_yoy DECIMAL(10, 4),  -- Year over year
    
    -- Data quality
    is_preliminary BOOLEAN DEFAULT FALSE,
    revision_number INTEGER DEFAULT 0,
    
    -- Source tracking
    data_source VARCHAR(50),
    
    CONSTRAINT uq_econ_indicator UNIQUE (series_id, observation_date)
);

-- Cleaned World Bank country indicators
CREATE TABLE IF NOT EXISTS silver.country_indicators (
    id BIGSERIAL PRIMARY KEY,
    processed_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- Country
    country_code VARCHAR(10) NOT NULL,
    country_name VARCHAR(200) NOT NULL,
    region VARCHAR(100),
    income_level VARCHAR(50),
    
    -- Indicator
    indicator_id VARCHAR(50) NOT NULL,
    indicator_name VARCHAR(500),
    
    -- Time
    year INTEGER NOT NULL,
    
    -- Value
    value DECIMAL(30, 10),
    
    -- Calculated
    pct_change_yoy DECIMAL(10, 4),
    
    CONSTRAINT uq_country_indicator UNIQUE (country_code, indicator_id, year)
);

-- Country dimension table
CREATE TABLE IF NOT EXISTS silver.dim_countries (
    id SERIAL PRIMARY KEY,
    
    country_code VARCHAR(10) NOT NULL UNIQUE,
    country_name VARCHAR(200) NOT NULL,
    iso3_code VARCHAR(3),
    
    region VARCHAR(100),
    sub_region VARCHAR(100),
    income_level VARCHAR(50),
    lending_type VARCHAR(50),
    
    capital_city VARCHAR(200),
    longitude DECIMAL(10, 6),
    latitude DECIMAL(10, 6),
    
    is_active BOOLEAN DEFAULT TRUE
);

-- Treasury yield curve data
CREATE TABLE IF NOT EXISTS silver.treasury_yields (
    id BIGSERIAL PRIMARY KEY,
    processed_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    record_date DATE NOT NULL,
    
    -- Yields by maturity
    yield_1m DECIMAL(10, 4),
    yield_3m DECIMAL(10, 4),
    yield_6m DECIMAL(10, 4),
    yield_1y DECIMAL(10, 4),
    yield_2y DECIMAL(10, 4),
    yield_3y DECIMAL(10, 4),
    yield_5y DECIMAL(10, 4),
    yield_7y DECIMAL(10, 4),
    yield_10y DECIMAL(10, 4),
    yield_20y DECIMAL(10, 4),
    yield_30y DECIMAL(10, 4),
    
    -- Yield curve spreads
    spread_10y_2y DECIMAL(10, 4),
    spread_10y_3m DECIMAL(10, 4),
    
    -- Inversion flag
    is_inverted BOOLEAN GENERATED ALWAYS AS (spread_10y_2y < 0) STORED,
    
    CONSTRAINT uq_treasury_yields UNIQUE (record_date)
);

-- US Debt statistics
CREATE TABLE IF NOT EXISTS silver.us_debt_stats (
    id BIGSERIAL PRIMARY KEY,
    processed_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    record_date DATE NOT NULL UNIQUE,
    
    total_public_debt_billions DECIMAL(20, 2),
    intragovernmental_billions DECIMAL(20, 2),
    debt_held_by_public_billions DECIMAL(20, 2),
    
    -- Debt to GDP ratio (joined with GDP data)
    debt_to_gdp_ratio DECIMAL(10, 4),
    
    -- Changes
    daily_change_billions DECIMAL(20, 2),
    yoy_change_pct DECIMAL(10, 4)
);

-- Employment statistics
CREATE TABLE IF NOT EXISTS silver.employment_stats (
    id BIGSERIAL PRIMARY KEY,
    processed_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    observation_date DATE NOT NULL UNIQUE,
    
    -- Unemployment
    unemployment_rate DECIMAL(6, 3),
    unemployment_level_thousands BIGINT,
    
    -- Employment
    employment_level_thousands BIGINT,
    nonfarm_payrolls_thousands BIGINT,
    labor_force_participation_rate DECIMAL(6, 3),
    
    -- Changes
    payrolls_change_thousands INTEGER,
    unemployment_rate_change DECIMAL(6, 4),
    
    -- Initial claims (weekly)
    initial_claims_thousands INTEGER
);

-- Inflation metrics
CREATE TABLE IF NOT EXISTS silver.inflation_metrics (
    id BIGSERIAL PRIMARY KEY,
    processed_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    observation_date DATE NOT NULL UNIQUE,
    
    -- CPI measures
    cpi_all_items DECIMAL(10, 3),
    cpi_core DECIMAL(10, 3),
    cpi_food DECIMAL(10, 3),
    cpi_energy DECIMAL(10, 3),
    cpi_shelter DECIMAL(10, 3),
    
    -- YoY inflation rates
    inflation_rate_yoy DECIMAL(6, 3),
    core_inflation_yoy DECIMAL(6, 3),
    
    -- MoM inflation rates
    inflation_rate_mom DECIMAL(6, 4),
    core_inflation_mom DECIMAL(6, 4),
    
    -- PCE measures (Fed preferred)
    pce_price_index DECIMAL(10, 3),
    pce_core DECIMAL(10, 3),
    pce_inflation_yoy DECIMAL(6, 3)
);

-- =============================================================================
-- TIME DIMENSION TABLE
-- =============================================================================

CREATE TABLE IF NOT EXISTS silver.dim_date (
    date_key INTEGER PRIMARY KEY,  -- YYYYMMDD format
    full_date DATE NOT NULL UNIQUE,
    
    -- Date parts
    year INTEGER NOT NULL,
    quarter INTEGER NOT NULL,
    month INTEGER NOT NULL,
    week_of_year INTEGER NOT NULL,
    day_of_month INTEGER NOT NULL,
    day_of_week INTEGER NOT NULL,
    day_of_year INTEGER NOT NULL,
    
    -- Names
    month_name VARCHAR(20) NOT NULL,
    day_name VARCHAR(20) NOT NULL,
    quarter_name VARCHAR(10) NOT NULL,
    
    -- Flags
    is_weekend BOOLEAN NOT NULL,
    is_us_holiday BOOLEAN DEFAULT FALSE,
    is_trading_day BOOLEAN DEFAULT TRUE,
    
    -- Fiscal calendar (Oct-Sep)
    fiscal_year INTEGER NOT NULL,
    fiscal_quarter INTEGER NOT NULL
);

-- =============================================================================
-- INDEXES
-- =============================================================================

-- Crypto indexes
CREATE INDEX IF NOT EXISTS idx_crypto_daily_coin_date ON silver.crypto_prices_daily(coin_id, price_date);
CREATE INDEX IF NOT EXISTS idx_crypto_hourly_coin_hour ON silver.crypto_prices_hourly(coin_id, price_hour);
CREATE INDEX IF NOT EXISTS idx_sentiment_date ON silver.market_sentiment(sentiment_date);
CREATE INDEX IF NOT EXISTS idx_btc_network_date ON silver.bitcoin_network_stats(stat_date);

-- Economic indexes
CREATE INDEX IF NOT EXISTS idx_econ_ind_series_date ON silver.economic_indicators(series_id, observation_date);
CREATE INDEX IF NOT EXISTS idx_country_ind_code_year ON silver.country_indicators(country_code, indicator_id, year);
CREATE INDEX IF NOT EXISTS idx_treasury_date ON silver.treasury_yields(record_date);
CREATE INDEX IF NOT EXISTS idx_employment_date ON silver.employment_stats(observation_date);
CREATE INDEX IF NOT EXISTS idx_inflation_date ON silver.inflation_metrics(observation_date);

-- Date dimension index
CREATE INDEX IF NOT EXISTS idx_dim_date_year_month ON silver.dim_date(year, month);

-- =============================================================================
-- COMMENTS
-- =============================================================================

COMMENT ON SCHEMA silver IS 'Cleaned and standardized data layer';
COMMENT ON TABLE silver.crypto_prices_daily IS 'Daily cryptocurrency prices, cleaned and standardized';
COMMENT ON TABLE silver.economic_indicators IS 'Cleaned economic indicator data from FRED and other sources';
COMMENT ON TABLE silver.dim_date IS 'Date dimension table for analytics';
