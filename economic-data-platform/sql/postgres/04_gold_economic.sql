-- =============================================================================
-- GOLD SCHEMA - ECONOMIC MART
-- Economic Data Analytics Platform
-- =============================================================================
-- Analytics-ready tables for economic data analysis
-- =============================================================================

-- Create Gold Economic Schema
CREATE SCHEMA IF NOT EXISTS gold_economic;

SET search_path TO gold_economic, silver, public;

-- =============================================================================
-- FACT TABLES
-- =============================================================================

-- US Economic indicators fact table
CREATE TABLE IF NOT EXISTS gold_economic.fct_us_indicators (
    id BIGSERIAL PRIMARY KEY,
    
    observation_date DATE NOT NULL,
    date_key INTEGER,
    
    -- GDP
    gdp_billions DECIMAL(20, 2),
    gdp_growth_qoq DECIMAL(6, 3),
    gdp_growth_yoy DECIMAL(6, 3),
    real_gdp_billions DECIMAL(20, 2),
    
    -- Employment
    unemployment_rate DECIMAL(6, 3),
    nonfarm_payrolls_thousands BIGINT,
    payrolls_change_monthly INTEGER,
    labor_force_participation DECIMAL(6, 3),
    initial_claims_thousands INTEGER,
    
    -- Inflation
    cpi_yoy DECIMAL(6, 3),
    core_cpi_yoy DECIMAL(6, 3),
    pce_yoy DECIMAL(6, 3),
    core_pce_yoy DECIMAL(6, 3),
    
    -- Interest Rates
    fed_funds_rate DECIMAL(6, 4),
    treasury_10y DECIMAL(6, 4),
    treasury_2y DECIMAL(6, 4),
    yield_curve_spread DECIMAL(6, 4),
    
    -- Money Supply
    m2_billions DECIMAL(20, 2),
    m2_growth_yoy DECIMAL(6, 3),
    
    -- Consumer
    retail_sales_billions DECIMAL(20, 2),
    consumer_sentiment DECIMAL(8, 2),
    pce_billions DECIMAL(20, 2),
    
    -- Housing
    housing_starts_thousands INTEGER,
    mortgage_rate_30y DECIMAL(6, 4),
    case_shiller_index DECIMAL(10, 2),
    
    -- Trade
    trade_balance_billions DECIMAL(20, 2),
    
    CONSTRAINT uq_us_indicators UNIQUE (observation_date)
);

-- International economic indicators
CREATE TABLE IF NOT EXISTS gold_economic.fct_global_indicators (
    id BIGSERIAL PRIMARY KEY,
    
    country_code VARCHAR(10) NOT NULL,
    year INTEGER NOT NULL,
    
    -- GDP
    gdp_usd_billions DECIMAL(20, 2),
    gdp_growth_pct DECIMAL(6, 3),
    gdp_per_capita_usd DECIMAL(20, 2),
    gdp_per_capita_ppp DECIMAL(20, 2),
    
    -- Population
    population_millions DECIMAL(15, 3),
    population_growth_pct DECIMAL(6, 3),
    
    -- Employment
    unemployment_rate DECIMAL(6, 3),
    labor_force_participation DECIMAL(6, 3),
    
    -- Inflation
    inflation_rate DECIMAL(6, 3),
    
    -- Trade
    trade_pct_of_gdp DECIMAL(6, 3),
    exports_pct_of_gdp DECIMAL(6, 3),
    imports_pct_of_gdp DECIMAL(6, 3),
    current_account_pct_of_gdp DECIMAL(6, 3),
    
    -- Government
    govt_debt_pct_of_gdp DECIMAL(8, 3),
    govt_revenue_pct_of_gdp DECIMAL(6, 3),
    govt_spending_pct_of_gdp DECIMAL(6, 3),
    
    -- Development
    gini_index DECIMAL(6, 3),
    hdi_score DECIMAL(5, 3),
    
    CONSTRAINT uq_global_indicators UNIQUE (country_code, year)
);

-- Treasury yield curve
CREATE TABLE IF NOT EXISTS gold_economic.fct_yield_curve (
    id BIGSERIAL PRIMARY KEY,
    
    curve_date DATE NOT NULL UNIQUE,
    date_key INTEGER,
    
    -- Short-term
    yield_1m DECIMAL(6, 4),
    yield_3m DECIMAL(6, 4),
    yield_6m DECIMAL(6, 4),
    
    -- Medium-term
    yield_1y DECIMAL(6, 4),
    yield_2y DECIMAL(6, 4),
    yield_3y DECIMAL(6, 4),
    yield_5y DECIMAL(6, 4),
    yield_7y DECIMAL(6, 4),
    
    -- Long-term
    yield_10y DECIMAL(6, 4),
    yield_20y DECIMAL(6, 4),
    yield_30y DECIMAL(6, 4),
    
    -- Spreads
    spread_2y_3m DECIMAL(6, 4),
    spread_10y_2y DECIMAL(6, 4),
    spread_10y_3m DECIMAL(6, 4),
    spread_30y_10y DECIMAL(6, 4),
    
    -- Curve shape
    is_inverted BOOLEAN,
    inversion_depth DECIMAL(6, 4),  -- Most negative spread
    
    -- Changes
    yield_10y_change_1d DECIMAL(6, 4),
    yield_10y_change_1w DECIMAL(6, 4),
    yield_10y_change_1m DECIMAL(6, 4)
);

-- US National debt
CREATE TABLE IF NOT EXISTS gold_economic.fct_us_debt (
    id BIGSERIAL PRIMARY KEY,
    
    record_date DATE NOT NULL UNIQUE,
    date_key INTEGER,
    
    -- Debt levels
    total_debt_billions DECIMAL(20, 2),
    debt_held_by_public_billions DECIMAL(20, 2),
    intragovernmental_billions DECIMAL(20, 2),
    
    -- Debt composition
    marketable_debt_billions DECIMAL(20, 2),
    nonmarketable_debt_billions DECIMAL(20, 2),
    
    -- Ratios
    debt_to_gdp_ratio DECIMAL(8, 4),
    interest_to_revenue_ratio DECIMAL(8, 4),
    
    -- Changes
    daily_change_billions DECIMAL(20, 2),
    mtd_change_billions DECIMAL(20, 2),
    ytd_change_billions DECIMAL(20, 2),
    yoy_change_pct DECIMAL(8, 4),
    
    -- Per capita
    debt_per_capita_usd DECIMAL(20, 2)
);

-- =============================================================================
-- DIMENSION TABLES
-- =============================================================================

-- Economic indicator dimension
CREATE TABLE IF NOT EXISTS gold_economic.dim_indicators (
    indicator_key SERIAL PRIMARY KEY,
    
    indicator_id VARCHAR(50) NOT NULL UNIQUE,
    indicator_name VARCHAR(500) NOT NULL,
    
    -- Classification
    category VARCHAR(100),
    subcategory VARCHAR(100),
    
    -- Metadata
    description TEXT,
    units VARCHAR(200),
    frequency VARCHAR(20),
    seasonal_adjustment VARCHAR(200),
    
    -- Source
    data_source VARCHAR(100),
    source_url VARCHAR(500),
    
    -- Typical values
    typical_min DECIMAL(30, 10),
    typical_max DECIMAL(30, 10),
    
    is_active BOOLEAN DEFAULT TRUE
);

-- Country dimension (enhanced)
CREATE TABLE IF NOT EXISTS gold_economic.dim_countries (
    country_key SERIAL PRIMARY KEY,
    
    country_code VARCHAR(10) NOT NULL UNIQUE,
    country_name VARCHAR(200) NOT NULL,
    iso3_code VARCHAR(3),
    
    -- Geography
    region VARCHAR(100),
    sub_region VARCHAR(100),
    continent VARCHAR(50),
    
    -- Classification
    income_level VARCHAR(50),
    lending_type VARCHAR(50),
    
    -- Metadata
    capital_city VARCHAR(200),
    currency_code VARCHAR(3),
    currency_name VARCHAR(100),
    
    -- Location
    longitude DECIMAL(10, 6),
    latitude DECIMAL(10, 6),
    area_sq_km DECIMAL(15, 2),
    
    -- Status
    is_active BOOLEAN DEFAULT TRUE
);

-- =============================================================================
-- AGGREGATE TABLES
-- =============================================================================

-- Monthly economic summary
CREATE TABLE IF NOT EXISTS gold_economic.agg_us_monthly (
    id BIGSERIAL PRIMARY KEY,
    
    year INTEGER NOT NULL,
    month INTEGER NOT NULL,
    
    -- GDP (interpolated for months)
    gdp_growth_yoy DECIMAL(6, 3),
    
    -- Employment (monthly data)
    unemployment_rate DECIMAL(6, 3),
    payrolls_change INTEGER,
    initial_claims_avg INTEGER,
    
    -- Inflation
    cpi_yoy DECIMAL(6, 3),
    core_cpi_yoy DECIMAL(6, 3),
    pce_yoy DECIMAL(6, 3),
    
    -- Rates
    fed_funds_rate_avg DECIMAL(6, 4),
    treasury_10y_avg DECIMAL(6, 4),
    mortgage_30y_avg DECIMAL(6, 4),
    
    -- Market
    sp500_return_pct DECIMAL(6, 4),
    
    CONSTRAINT uq_us_monthly UNIQUE (year, month)
);

-- Quarterly economic summary
CREATE TABLE IF NOT EXISTS gold_economic.agg_us_quarterly (
    id BIGSERIAL PRIMARY KEY,
    
    year INTEGER NOT NULL,
    quarter INTEGER NOT NULL,
    
    -- GDP
    gdp_billions DECIMAL(20, 2),
    real_gdp_billions DECIMAL(20, 2),
    gdp_growth_qoq_annualized DECIMAL(6, 3),
    gdp_growth_yoy DECIMAL(6, 3),
    
    -- GDP Components (contribution to growth)
    consumption_contribution DECIMAL(6, 3),
    investment_contribution DECIMAL(6, 3),
    govt_contribution DECIMAL(6, 3),
    net_exports_contribution DECIMAL(6, 3),
    
    -- Quarter averages
    unemployment_rate_avg DECIMAL(6, 3),
    inflation_avg DECIMAL(6, 3),
    fed_funds_rate_avg DECIMAL(6, 4),
    
    CONSTRAINT uq_us_quarterly UNIQUE (year, quarter)
);

-- Annual economic summary
CREATE TABLE IF NOT EXISTS gold_economic.agg_us_annual (
    id BIGSERIAL PRIMARY KEY,
    
    year INTEGER NOT NULL UNIQUE,
    
    -- GDP
    gdp_billions DECIMAL(20, 2),
    real_gdp_billions DECIMAL(20, 2),
    gdp_growth_pct DECIMAL(6, 3),
    gdp_per_capita DECIMAL(20, 2),
    
    -- Employment
    unemployment_rate_avg DECIMAL(6, 3),
    total_jobs_added INTEGER,
    
    -- Inflation
    cpi_annual_avg DECIMAL(6, 3),
    
    -- Rates
    fed_funds_rate_avg DECIMAL(6, 4),
    fed_funds_rate_eoy DECIMAL(6, 4),
    
    -- Debt
    national_debt_billions DECIMAL(20, 2),
    debt_to_gdp_ratio DECIMAL(8, 4),
    
    -- Markets
    sp500_return_pct DECIMAL(6, 3),
    
    -- Population
    population_millions DECIMAL(10, 3)
);

-- Global comparison
CREATE TABLE IF NOT EXISTS gold_economic.agg_global_comparison (
    id BIGSERIAL PRIMARY KEY,
    
    year INTEGER NOT NULL,
    
    -- Global aggregates
    world_gdp_trillions DECIMAL(15, 2),
    world_population_billions DECIMAL(10, 3),
    world_gdp_per_capita DECIMAL(20, 2),
    
    -- Top economies share
    g7_gdp_share_pct DECIMAL(6, 3),
    g20_gdp_share_pct DECIMAL(6, 3),
    
    -- Growth leaders
    fastest_growing_economy VARCHAR(10),
    fastest_growth_rate DECIMAL(6, 3),
    
    -- Rankings snapshot
    top_10_by_gdp VARCHAR(200),  -- Comma-separated country codes
    
    CONSTRAINT uq_global_comparison UNIQUE (year)
);

-- =============================================================================
-- INDEXES
-- =============================================================================

CREATE INDEX IF NOT EXISTS idx_us_ind_date ON gold_economic.fct_us_indicators(observation_date DESC);
CREATE INDEX IF NOT EXISTS idx_global_ind_country ON gold_economic.fct_global_indicators(country_code, year DESC);
CREATE INDEX IF NOT EXISTS idx_yield_date ON gold_economic.fct_yield_curve(curve_date DESC);
CREATE INDEX IF NOT EXISTS idx_debt_date ON gold_economic.fct_us_debt(record_date DESC);

-- =============================================================================
-- COMMENTS
-- =============================================================================

COMMENT ON SCHEMA gold_economic IS 'Economic analytics mart - ready for dashboards and analysis';
COMMENT ON TABLE gold_economic.fct_us_indicators IS 'Consolidated US economic indicators';
COMMENT ON TABLE gold_economic.fct_yield_curve IS 'Treasury yield curve with spreads and signals';
