{{
    config(
        materialized='table',
        tags=['combined', 'mart', 'cross_domain', 'analytics']
    )
}}

with btc_macro as (
    select * from {{ ref('int_btc_macro_correlation') }}
),

crypto_analytics as (
    select * from {{ ref('fct_crypto_daily_analytics') }}
    where symbol = 'BTCUSDT'
),

economic_analytics as (
    select * from {{ ref('fct_economic_indicators') }}
),

-- Combine all analytics
combined_analytics as (
    select
        bm.date,
        
        -- Bitcoin metrics
        bm.btc_close,
        bm.btc_price_change_pct,
        bm.btc_volatility_pct,
        ca.ma_7d as btc_ma_7d,
        ca.ma_30d as btc_ma_30d,
        ca.trend_signal as btc_trend,
        ca.volume_signal as btc_volume_signal,
        
        -- Economic indicators
        bm.inflation_rate_yoy,
        bm.unemployment_rate,
        bm.federal_funds_rate,
        bm.treasury_10y_rate,
        bm.real_interest_rate,
        bm.m2_growth_rate_yoy,
        bm.gdp_growth_rate_yoy,
        
        -- Economic classifications
        ea.economic_regime,
        ea.monetary_policy_stance,
        ea.labor_market_health,
        ea.inflation_trend,
        ea.rate_trend,
        
        -- Cross-domain relationships
        bm.inflation_btc_relationship,
        bm.rate_environment,
        bm.money_supply_regime,
        
        -- Derived insights
        case 
            when bm.inflation_rate_yoy > 3 and bm.btc_price_change_pct > 0 
            then 'btc_inflation_hedge_working'
            when bm.inflation_rate_yoy > 3 and bm.btc_price_change_pct < 0 
            then 'btc_inflation_hedge_failing'
            else 'neutral_inflation_environment'
        end as inflation_hedge_status,
        
        case 
            when bm.federal_funds_rate > 4 and bm.btc_price_change_pct < 0 
            then 'rate_pressure_negative'
            when bm.federal_funds_rate < 2 and bm.btc_price_change_pct > 0 
            then 'rate_environment_positive'
            else 'neutral_rate_impact'
        end as rate_impact_on_btc,
        
        case 
            when bm.m2_growth_rate_yoy > 10 and bm.btc_price_change_pct > 0 
            then 'money_printing_bullish'
            when bm.m2_growth_rate_yoy < 0 and bm.btc_price_change_pct < 0 
            then 'money_contraction_bearish'
            else 'neutral_money_supply'
        end as money_supply_impact,
        
        -- Risk assessment
        case 
            when ea.economic_regime = 'recession' and bm.btc_volatility_pct > 5 
            then 'high_risk'
            when ea.economic_regime = 'goldilocks' and bm.btc_volatility_pct < 3 
            then 'low_risk'
            else 'moderate_risk'
        end as market_risk_level,
        
        current_timestamp as processed_at
        
    from btc_macro bm
    left join crypto_analytics ca
        on bm.date = ca.trade_date
    left join economic_analytics ea
        on bm.date = ea.observation_date
),

with_correlations as (
    select
        *,
        
        -- Calculate 30-day rolling correlation approximations
        corr(btc_price_change_pct, inflation_rate_yoy) over (
            order by date 
            rows between 29 preceding and current row
        ) as btc_inflation_correlation_30d,
        
        corr(btc_price_change_pct, federal_funds_rate) over (
            order by date 
            rows between 29 preceding and current row
        ) as btc_rates_correlation_30d,
        
        corr(btc_price_change_pct, m2_growth_rate_yoy) over (
            order by date 
            rows between 29 preceding and current row
        ) as btc_m2_correlation_30d,
        
        -- Regime persistence (days in current regime)
        row_number() over (
            partition by economic_regime 
            order by date
        ) as days_in_economic_regime,
        
        row_number() over (
            partition by monetary_policy_stance 
            order by date
        ) as days_in_policy_stance
        
    from combined_analytics
)

select * from with_correlations
