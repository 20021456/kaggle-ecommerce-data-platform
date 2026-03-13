-- =============================================================================
-- GOLD SCHEMA - CRYPTO MART
-- Economic Data Analytics Platform
-- =============================================================================
-- Analytics-ready tables for crypto market analysis
-- =============================================================================

-- Create Gold Crypto Schema
CREATE SCHEMA IF NOT EXISTS gold_crypto;

SET search_path TO gold_crypto, silver, public;

-- =============================================================================
-- FACT TABLES
-- =============================================================================

-- Daily crypto trading facts
CREATE TABLE IF NOT EXISTS gold_crypto.fct_crypto_daily (
    id BIGSERIAL PRIMARY KEY,
    
    -- Dimensions
    coin_id VARCHAR(100) NOT NULL,
    price_date DATE NOT NULL,
    date_key INTEGER,  -- FK to dim_date
    
    -- Prices
    open_price DECIMAL(30, 10),
    high_price DECIMAL(30, 10),
    low_price DECIMAL(30, 10),
    close_price DECIMAL(30, 10),
    
    -- Volume & Market Cap
    volume_usd DECIMAL(30, 2),
    market_cap_usd DECIMAL(30, 2),
    
    -- Price metrics
    daily_return_pct DECIMAL(10, 6),
    daily_range_pct DECIMAL(10, 4),  -- (high-low)/close
    
    -- Moving averages
    sma_7d DECIMAL(30, 10),
    sma_30d DECIMAL(30, 10),
    sma_50d DECIMAL(30, 10),
    sma_200d DECIMAL(30, 10),
    
    -- Volatility (rolling)
    volatility_7d DECIMAL(10, 6),
    volatility_30d DECIMAL(10, 6),
    
    -- RSI (Relative Strength Index)
    rsi_14d DECIMAL(6, 2),
    
    -- Trend signals
    is_above_sma_50 BOOLEAN,
    is_above_sma_200 BOOLEAN,
    golden_cross_signal BOOLEAN,  -- SMA50 crosses above SMA200
    death_cross_signal BOOLEAN,   -- SMA50 crosses below SMA200
    
    -- Volume analysis
    volume_sma_20d DECIMAL(30, 2),
    is_high_volume BOOLEAN,  -- Volume > 2x SMA20
    
    CONSTRAINT uq_fct_crypto_daily UNIQUE (coin_id, price_date)
);

-- Hourly trading facts (for real-time analysis)
CREATE TABLE IF NOT EXISTS gold_crypto.fct_crypto_hourly (
    id BIGSERIAL PRIMARY KEY,
    
    coin_id VARCHAR(100) NOT NULL,
    price_hour TIMESTAMP WITH TIME ZONE NOT NULL,
    
    open_price DECIMAL(30, 10),
    high_price DECIMAL(30, 10),
    low_price DECIMAL(30, 10),
    close_price DECIMAL(30, 10),
    volume_usd DECIMAL(30, 2),
    trades_count INTEGER,
    
    -- Hourly metrics
    hourly_return_pct DECIMAL(10, 6),
    vwap DECIMAL(30, 10),  -- Volume weighted average price
    
    -- Short-term MAs
    ema_12h DECIMAL(30, 10),
    ema_24h DECIMAL(30, 10),
    
    CONSTRAINT uq_fct_crypto_hourly UNIQUE (coin_id, price_hour)
);

-- Market sentiment facts
CREATE TABLE IF NOT EXISTS gold_crypto.fct_market_sentiment (
    id BIGSERIAL PRIMARY KEY,
    
    sentiment_date DATE NOT NULL UNIQUE,
    date_key INTEGER,
    
    -- Fear & Greed
    fear_greed_value INTEGER,
    fear_greed_classification VARCHAR(50),
    fear_greed_ma_7d DECIMAL(6, 2),
    fear_greed_ma_30d DECIMAL(6, 2),
    
    -- Sentiment metrics
    sentiment_score DECIMAL(5, 4),  -- Normalized -1 to 1
    sentiment_change_1d DECIMAL(5, 4),
    sentiment_change_7d DECIMAL(5, 4),
    
    -- Extremes
    is_extreme_fear BOOLEAN,  -- < 20
    is_extreme_greed BOOLEAN, -- > 80
    
    -- Trading signals
    contrarian_signal VARCHAR(20)  -- 'buy', 'sell', 'hold'
);

-- Bitcoin on-chain metrics
CREATE TABLE IF NOT EXISTS gold_crypto.fct_bitcoin_onchain (
    id BIGSERIAL PRIMARY KEY,
    
    metric_date DATE NOT NULL UNIQUE,
    date_key INTEGER,
    
    -- Network activity
    hash_rate_eh DECIMAL(20, 2),
    hash_rate_change_pct DECIMAL(10, 4),
    difficulty DECIMAL(30, 2),
    block_height BIGINT,
    
    -- Supply metrics
    total_btc DECIMAL(20, 8),
    daily_issuance DECIMAL(20, 8),
    issuance_rate_pct DECIMAL(10, 6),  -- Annual inflation
    
    -- Transaction activity
    transactions_count BIGINT,
    avg_transaction_value_btc DECIMAL(20, 8),
    transaction_fees_btc DECIMAL(20, 8),
    
    -- Miners
    miners_revenue_usd DECIMAL(20, 2),
    hash_price DECIMAL(20, 6),  -- Revenue per TH/s
    
    -- Stock-to-Flow
    stock_to_flow DECIMAL(10, 2),
    s2f_model_price DECIMAL(30, 2)
);

-- =============================================================================
-- DIMENSION TABLES
-- =============================================================================

-- Coin dimension
CREATE TABLE IF NOT EXISTS gold_crypto.dim_coins (
    coin_key SERIAL PRIMARY KEY,
    
    coin_id VARCHAR(100) NOT NULL UNIQUE,
    symbol VARCHAR(20) NOT NULL,
    name VARCHAR(200) NOT NULL,
    
    -- Classification
    asset_type VARCHAR(50),  -- 'cryptocurrency', 'token', 'stablecoin'
    category VARCHAR(100),
    platform VARCHAR(100),  -- e.g., 'Ethereum', 'Solana'
    
    -- Metadata
    genesis_date DATE,
    description TEXT,
    website_url VARCHAR(500),
    
    -- Current stats (updated daily)
    current_price_usd DECIMAL(30, 10),
    market_cap_usd DECIMAL(30, 2),
    market_cap_rank INTEGER,
    
    -- Supply
    circulating_supply DECIMAL(30, 2),
    total_supply DECIMAL(30, 2),
    max_supply DECIMAL(30, 2),
    
    -- Status
    is_active BOOLEAN DEFAULT TRUE,
    last_updated TIMESTAMP WITH TIME ZONE
);

-- =============================================================================
-- AGGREGATE TABLES
-- =============================================================================

-- Weekly crypto summary
CREATE TABLE IF NOT EXISTS gold_crypto.agg_crypto_weekly (
    id BIGSERIAL PRIMARY KEY,
    
    coin_id VARCHAR(100) NOT NULL,
    week_start_date DATE NOT NULL,
    week_end_date DATE NOT NULL,
    
    -- OHLC for the week
    open_price DECIMAL(30, 10),
    high_price DECIMAL(30, 10),
    low_price DECIMAL(30, 10),
    close_price DECIMAL(30, 10),
    
    -- Volume
    total_volume_usd DECIMAL(30, 2),
    avg_daily_volume DECIMAL(30, 2),
    
    -- Returns
    weekly_return_pct DECIMAL(10, 6),
    
    -- Volatility
    weekly_volatility DECIMAL(10, 6),
    
    CONSTRAINT uq_crypto_weekly UNIQUE (coin_id, week_start_date)
);

-- Monthly crypto summary
CREATE TABLE IF NOT EXISTS gold_crypto.agg_crypto_monthly (
    id BIGSERIAL PRIMARY KEY,
    
    coin_id VARCHAR(100) NOT NULL,
    year INTEGER NOT NULL,
    month INTEGER NOT NULL,
    
    -- OHLC for the month
    open_price DECIMAL(30, 10),
    high_price DECIMAL(30, 10),
    low_price DECIMAL(30, 10),
    close_price DECIMAL(30, 10),
    
    -- Volume
    total_volume_usd DECIMAL(30, 2),
    avg_daily_volume DECIMAL(30, 2),
    trading_days INTEGER,
    
    -- Returns
    monthly_return_pct DECIMAL(10, 6),
    
    -- Volatility
    monthly_volatility DECIMAL(10, 6),
    
    CONSTRAINT uq_crypto_monthly UNIQUE (coin_id, year, month)
);

-- Market overview (all crypto)
CREATE TABLE IF NOT EXISTS gold_crypto.agg_market_daily (
    id BIGSERIAL PRIMARY KEY,
    
    market_date DATE NOT NULL UNIQUE,
    
    -- Total market
    total_market_cap_usd DECIMAL(30, 2),
    total_volume_24h_usd DECIMAL(30, 2),
    
    -- Bitcoin dominance
    btc_dominance_pct DECIMAL(6, 2),
    eth_dominance_pct DECIMAL(6, 2),
    
    -- Market breadth
    coins_gainers INTEGER,
    coins_losers INTEGER,
    advance_decline_ratio DECIMAL(10, 4),
    
    -- Largest gainers/losers
    top_gainer_id VARCHAR(100),
    top_gainer_pct DECIMAL(10, 4),
    top_loser_id VARCHAR(100),
    top_loser_pct DECIMAL(10, 4)
);

-- =============================================================================
-- INDEXES
-- =============================================================================

CREATE INDEX IF NOT EXISTS idx_fct_daily_coin_date ON gold_crypto.fct_crypto_daily(coin_id, price_date DESC);
CREATE INDEX IF NOT EXISTS idx_fct_daily_date ON gold_crypto.fct_crypto_daily(price_date DESC);
CREATE INDEX IF NOT EXISTS idx_fct_hourly_coin ON gold_crypto.fct_crypto_hourly(coin_id, price_hour DESC);
CREATE INDEX IF NOT EXISTS idx_sentiment_date ON gold_crypto.fct_market_sentiment(sentiment_date DESC);
CREATE INDEX IF NOT EXISTS idx_onchain_date ON gold_crypto.fct_bitcoin_onchain(metric_date DESC);

-- =============================================================================
-- COMMENTS
-- =============================================================================

COMMENT ON SCHEMA gold_crypto IS 'Crypto analytics mart - ready for dashboards and analysis';
COMMENT ON TABLE gold_crypto.fct_crypto_daily IS 'Daily crypto prices with technical indicators';
COMMENT ON TABLE gold_crypto.dim_coins IS 'Cryptocurrency dimension with metadata';
