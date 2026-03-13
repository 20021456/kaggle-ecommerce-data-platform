-- =============================================================================
-- GOLD SCHEMA - COMBINED ANALYTICS
-- Economic Data Analytics Platform
-- =============================================================================
-- Cross-domain analytics combining crypto and economic data
-- =============================================================================

-- Create Combined Analytics Schema
CREATE SCHEMA IF NOT EXISTS gold_combined;

SET search_path TO gold_combined, gold_crypto, gold_economic, silver, public;

-- =============================================================================
-- CROSS-DOMAIN FACT TABLES
-- =============================================================================

-- Daily crypto with macro context
CREATE TABLE IF NOT EXISTS gold_combined.fct_crypto_macro_daily (
    id BIGSERIAL PRIMARY KEY,
    
    observation_date DATE NOT NULL,
    date_key INTEGER,
    
    -- Bitcoin data
    btc_price_usd DECIMAL(30, 10),
    btc_return_daily_pct DECIMAL(10, 6),
    btc_volatility_30d DECIMAL(10, 6),
    btc_volume_usd DECIMAL(30, 2),
    btc_market_cap_usd DECIMAL(30, 2),
    
    -- Market sentiment
    fear_greed_value INTEGER,
    fear_greed_classification VARCHAR(50),
    
    -- Macro indicators (latest available)
    unemployment_rate DECIMAL(6, 3),
    cpi_yoy DECIMAL(6, 3),
    core_cpi_yoy DECIMAL(6, 3),
    fed_funds_rate DECIMAL(6, 4),
    treasury_10y DECIMAL(6, 4),
    yield_curve_spread DECIMAL(6, 4),
    
    -- S&P 500
    sp500_close DECIMAL(20, 2),
    sp500_return_daily_pct DECIMAL(10, 6),
    
    -- Gold
    gold_price_usd DECIMAL(20, 2),
    gold_return_daily_pct DECIMAL(10, 6),
    
    -- Dollar
    dxy_index DECIMAL(10, 4),  -- US Dollar Index
    
    -- M2 Money Supply
    m2_billions DECIMAL(20, 2),
    m2_growth_yoy DECIMAL(6, 3),
    
    -- Correlations (rolling 30-day)
    btc_sp500_corr_30d DECIMAL(6, 4),
    btc_gold_corr_30d DECIMAL(6, 4),
    btc_dxy_corr_30d DECIMAL(6, 4),
    
    CONSTRAINT uq_crypto_macro_daily UNIQUE (observation_date)
);

-- Bitcoin vs Inflation analysis
CREATE TABLE IF NOT EXISTS gold_combined.analysis_btc_inflation (
    id BIGSERIAL PRIMARY KEY,
    
    observation_date DATE NOT NULL,
    
    -- Bitcoin
    btc_price_usd DECIMAL(30, 10),
    btc_return_1y_pct DECIMAL(10, 4),
    
    -- Inflation
    cpi_value DECIMAL(10, 3),
    inflation_rate_yoy DECIMAL(6, 3),
    core_inflation_yoy DECIMAL(6, 3),
    
    -- Real returns
    btc_real_return_1y_pct DECIMAL(10, 4),  -- BTC return minus inflation
    gold_real_return_1y_pct DECIMAL(10, 4),
    sp500_real_return_1y_pct DECIMAL(10, 4),
    
    -- BTC as inflation hedge metrics
    btc_inflation_beta DECIMAL(10, 4),  -- Regression coefficient
    inflation_hedge_score DECIMAL(6, 4),  -- Custom score
    
    -- Comparison to traditional hedges
    btc_vs_gold_return DECIMAL(10, 4),
    btc_vs_tips_return DECIMAL(10, 4),
    
    CONSTRAINT uq_btc_inflation UNIQUE (observation_date)
);

-- Bitcoin vs Interest Rates analysis
CREATE TABLE IF NOT EXISTS gold_combined.analysis_btc_rates (
    id BIGSERIAL PRIMARY KEY,
    
    observation_date DATE NOT NULL,
    
    -- Bitcoin
    btc_price_usd DECIMAL(30, 10),
    btc_return_mtd_pct DECIMAL(10, 4),
    btc_return_ytd_pct DECIMAL(10, 4),
    
    -- Interest rates
    fed_funds_rate DECIMAL(6, 4),
    fed_funds_change_mtd DECIMAL(6, 4),
    treasury_10y DECIMAL(6, 4),
    treasury_2y DECIMAL(6, 4),
    real_rate_10y DECIMAL(6, 4),  -- 10Y minus CPI
    
    -- Rate environment
    rate_regime VARCHAR(50),  -- 'hiking', 'cutting', 'pause'
    months_since_last_change INTEGER,
    
    -- BTC sensitivity to rates
    btc_rate_sensitivity DECIMAL(10, 4),
    
    -- Performance by regime
    btc_return_in_regime_pct DECIMAL(10, 4),
    
    CONSTRAINT uq_btc_rates UNIQUE (observation_date)
);

-- Market regime classification
CREATE TABLE IF NOT EXISTS gold_combined.analysis_market_regime (
    id BIGSERIAL PRIMARY KEY,
    
    regime_date DATE NOT NULL UNIQUE,
    
    -- Economic regime
    economic_cycle VARCHAR(50),  -- 'expansion', 'peak', 'contraction', 'trough'
    gdp_growth_trend VARCHAR(20),  -- 'accelerating', 'decelerating', 'stable'
    inflation_regime VARCHAR(50),  -- 'low', 'moderate', 'high', 'disinflation'
    
    -- Monetary policy
    fed_stance VARCHAR(50),  -- 'hawkish', 'neutral', 'dovish'
    liquidity_conditions VARCHAR(50),  -- 'tight', 'neutral', 'loose'
    
    -- Market conditions
    risk_appetite VARCHAR(50),  -- 'risk-on', 'neutral', 'risk-off'
    volatility_regime VARCHAR(50),  -- 'low', 'normal', 'high'
    
    -- Crypto specific
    crypto_market_phase VARCHAR(50),  -- 'bull', 'bear', 'accumulation', 'distribution'
    btc_trend VARCHAR(50),  -- 'uptrend', 'downtrend', 'sideways'
    
    -- Regime scores
    risk_score DECIMAL(5, 2),  -- 0-100
    opportunity_score DECIMAL(5, 2)  -- 0-100
);

-- Cross-asset correlation matrix
CREATE TABLE IF NOT EXISTS gold_combined.analysis_correlation_matrix (
    id BIGSERIAL PRIMARY KEY,
    
    calculation_date DATE NOT NULL,
    lookback_period VARCHAR(20) NOT NULL,  -- '30d', '90d', '1y'
    
    -- BTC correlations
    btc_eth_corr DECIMAL(6, 4),
    btc_sp500_corr DECIMAL(6, 4),
    btc_nasdaq_corr DECIMAL(6, 4),
    btc_gold_corr DECIMAL(6, 4),
    btc_dxy_corr DECIMAL(6, 4),
    btc_treasury10y_corr DECIMAL(6, 4),
    btc_oil_corr DECIMAL(6, 4),
    
    -- ETH correlations
    eth_sp500_corr DECIMAL(6, 4),
    eth_gold_corr DECIMAL(6, 4),
    
    -- Traditional asset correlations
    sp500_gold_corr DECIMAL(6, 4),
    sp500_treasury10y_corr DECIMAL(6, 4),
    gold_dxy_corr DECIMAL(6, 4),
    
    -- Correlation changes
    btc_sp500_corr_change_30d DECIMAL(6, 4),
    
    CONSTRAINT uq_corr_matrix UNIQUE (calculation_date, lookback_period)
);

-- =============================================================================
-- RESEARCH ANALYSIS TABLES
-- =============================================================================

-- Bitcoin as inflation hedge summary
CREATE TABLE IF NOT EXISTS gold_combined.research_btc_inflation_hedge (
    id BIGSERIAL PRIMARY KEY,
    
    analysis_date DATE NOT NULL,
    analysis_period VARCHAR(50) NOT NULL,  -- 'all_time', '2020-2024', etc.
    
    -- Summary statistics
    btc_total_return_pct DECIMAL(10, 4),
    gold_total_return_pct DECIMAL(10, 4),
    sp500_total_return_pct DECIMAL(10, 4),
    tips_total_return_pct DECIMAL(10, 4),
    
    -- Inflation-adjusted returns
    btc_real_return_pct DECIMAL(10, 4),
    gold_real_return_pct DECIMAL(10, 4),
    sp500_real_return_pct DECIMAL(10, 4),
    
    -- Correlation with inflation
    btc_cpi_correlation DECIMAL(6, 4),
    gold_cpi_correlation DECIMAL(6, 4),
    
    -- Regression results
    btc_inflation_beta DECIMAL(10, 4),
    btc_inflation_r_squared DECIMAL(6, 4),
    
    -- Conclusion
    is_effective_hedge BOOLEAN,
    hedge_effectiveness_score DECIMAL(5, 2),
    
    notes TEXT,
    
    CONSTRAINT uq_research_inflation UNIQUE (analysis_date, analysis_period)
);

-- Economic event impact on crypto
CREATE TABLE IF NOT EXISTS gold_combined.research_event_impact (
    id BIGSERIAL PRIMARY KEY,
    
    event_date DATE NOT NULL,
    event_type VARCHAR(100) NOT NULL,  -- 'fed_rate_decision', 'cpi_release', etc.
    event_description VARCHAR(500),
    
    -- Pre-event
    btc_price_pre DECIMAL(30, 10),
    sp500_pre DECIMAL(20, 2),
    
    -- Immediate reaction (same day)
    btc_return_0d_pct DECIMAL(10, 6),
    sp500_return_0d_pct DECIMAL(10, 6),
    
    -- Short-term (1 week)
    btc_return_1w_pct DECIMAL(10, 6),
    sp500_return_1w_pct DECIMAL(10, 6),
    
    -- Medium-term (1 month)
    btc_return_1m_pct DECIMAL(10, 6),
    sp500_return_1m_pct DECIMAL(10, 6),
    
    -- Event details
    expected_value VARCHAR(100),
    actual_value VARCHAR(100),
    surprise_direction VARCHAR(20),  -- 'hawkish', 'dovish', 'in_line'
    
    CONSTRAINT uq_event_impact UNIQUE (event_date, event_type)
);

-- =============================================================================
-- VIEWS FOR COMMON QUERIES
-- =============================================================================

-- Latest cross-domain snapshot
CREATE OR REPLACE VIEW gold_combined.vw_latest_snapshot AS
SELECT 
    cm.observation_date,
    cm.btc_price_usd,
    cm.btc_return_daily_pct,
    cm.fear_greed_value,
    cm.fear_greed_classification,
    cm.unemployment_rate,
    cm.cpi_yoy,
    cm.fed_funds_rate,
    cm.treasury_10y,
    cm.yield_curve_spread,
    cm.sp500_close,
    cm.gold_price_usd,
    cm.btc_sp500_corr_30d,
    cm.btc_gold_corr_30d,
    mr.economic_cycle,
    mr.fed_stance,
    mr.crypto_market_phase
FROM gold_combined.fct_crypto_macro_daily cm
LEFT JOIN gold_combined.analysis_market_regime mr ON cm.observation_date = mr.regime_date
ORDER BY cm.observation_date DESC
LIMIT 1;

-- Monthly performance comparison
CREATE OR REPLACE VIEW gold_combined.vw_monthly_performance AS
SELECT 
    DATE_TRUNC('month', observation_date) AS month,
    
    -- BTC
    (LAST_VALUE(btc_price_usd) OVER w - FIRST_VALUE(btc_price_usd) OVER w) 
        / FIRST_VALUE(btc_price_usd) OVER w * 100 AS btc_return_pct,
    
    -- S&P 500
    (LAST_VALUE(sp500_close) OVER w - FIRST_VALUE(sp500_close) OVER w) 
        / FIRST_VALUE(sp500_close) OVER w * 100 AS sp500_return_pct,
    
    -- Gold
    (LAST_VALUE(gold_price_usd) OVER w - FIRST_VALUE(gold_price_usd) OVER w) 
        / FIRST_VALUE(gold_price_usd) OVER w * 100 AS gold_return_pct,
    
    -- Average conditions
    AVG(fed_funds_rate) AS avg_fed_funds,
    AVG(cpi_yoy) AS avg_inflation
    
FROM gold_combined.fct_crypto_macro_daily
WINDOW w AS (PARTITION BY DATE_TRUNC('month', observation_date) 
             ORDER BY observation_date 
             ROWS BETWEEN UNBOUNDED PRECEDING AND UNBOUNDED FOLLOWING)
GROUP BY DATE_TRUNC('month', observation_date), btc_price_usd, sp500_close, gold_price_usd, fed_funds_rate, cpi_yoy
ORDER BY month DESC;

-- =============================================================================
-- INDEXES
-- =============================================================================

CREATE INDEX IF NOT EXISTS idx_crypto_macro_date ON gold_combined.fct_crypto_macro_daily(observation_date DESC);
CREATE INDEX IF NOT EXISTS idx_btc_inflation_date ON gold_combined.analysis_btc_inflation(observation_date DESC);
CREATE INDEX IF NOT EXISTS idx_btc_rates_date ON gold_combined.analysis_btc_rates(observation_date DESC);
CREATE INDEX IF NOT EXISTS idx_regime_date ON gold_combined.analysis_market_regime(regime_date DESC);
CREATE INDEX IF NOT EXISTS idx_corr_matrix_date ON gold_combined.analysis_correlation_matrix(calculation_date DESC);

-- =============================================================================
-- COMMENTS
-- =============================================================================

COMMENT ON SCHEMA gold_combined IS 'Cross-domain analytics combining crypto and economic data';
COMMENT ON TABLE gold_combined.fct_crypto_macro_daily IS 'Daily crypto prices with macro context';
COMMENT ON TABLE gold_combined.analysis_btc_inflation IS 'Bitcoin as inflation hedge analysis';
COMMENT ON TABLE gold_combined.analysis_market_regime IS 'Market regime classification';
