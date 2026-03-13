{{
    config(
        materialized='table',
        tags=['combined', 'intermediate', 'cross_domain']
    )
}}

with crypto_daily as (
    select * from {{ ref('int_crypto_daily_ohlcv') }}
    where symbol = 'BTCUSDT'
),

economic_indicators as (
    select * from {{ ref('int_economic_indicators_pivoted') }}
),

-- Join crypto and economic data by date
combined as (
    select
        c.trade_date as date,
        
        -- Crypto metrics (Bitcoin)
        c.symbol as crypto_symbol,
        c.open_price as btc_open,
        c.close_price as btc_close,
        c.high_price as btc_high,
        c.low_price as btc_low,
        c.avg_price as btc_avg_price,
        c.total_volume as btc_volume,
        c.total_value_usd as btc_value_usd,
        c.price_change_percentage as btc_price_change_pct,
        c.volatility_percentage as btc_volatility_pct,
        
        -- Economic indicators
        e.cpi_all_urban,
        e.inflation_rate_yoy,
        e.unemployment_rate,
        e.federal_funds_rate,
        e.treasury_10y_rate,
        e.real_interest_rate,
        e.m2_money_supply,
        e.m2_growth_rate_yoy,
        e.gdp_real_chained,
        e.gdp_growth_rate_yoy,
        
        current_timestamp as processed_at
        
    from crypto_daily c
    left join economic_indicators e
        on c.trade_date = e.observation_date
),

with_correlations as (
    select
        *,
        
        -- Calculate rolling correlations (simplified - in production use window functions)
        -- Inflation hedge analysis
        case 
            when inflation_rate_yoy > 3 and btc_price_change_pct > 0 then 'positive_inflation_btc_up'
            when inflation_rate_yoy > 3 and btc_price_change_pct < 0 then 'positive_inflation_btc_down'
            when inflation_rate_yoy < 2 and btc_price_change_pct > 0 then 'low_inflation_btc_up'
            when inflation_rate_yoy < 2 and btc_price_change_pct < 0 then 'low_inflation_btc_down'
            else 'neutral'
        end as inflation_btc_relationship,
        
        -- Interest rate impact
        case 
            when federal_funds_rate > 4 then 'high_rates'
            when federal_funds_rate > 2 then 'moderate_rates'
            else 'low_rates'
        end as rate_environment,
        
        -- Money supply impact
        case 
            when m2_growth_rate_yoy > 10 then 'high_money_growth'
            when m2_growth_rate_yoy > 5 then 'moderate_money_growth'
            when m2_growth_rate_yoy < 0 then 'money_contraction'
            else 'stable_money_growth'
        end as money_supply_regime
        
    from combined
)

select * from with_correlations
