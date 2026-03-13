{{
    config(
        materialized='table',
        tags=['economic', 'mart', 'analytics']
    )
}}

with economic_indicators as (
    select * from {{ ref('int_economic_indicators_pivoted') }}
),

with_trends as (
    select
        observation_date,
        observation_year,
        observation_month,
        observation_quarter,
        
        -- Core indicators
        cpi_all_urban,
        inflation_rate_yoy,
        unemployment_rate,
        federal_funds_rate,
        treasury_10y_rate,
        real_interest_rate,
        m2_money_supply,
        m2_growth_rate_yoy,
        gdp_real_chained,
        gdp_growth_rate_yoy,
        
        -- Trend analysis (3-month moving averages)
        avg(inflation_rate_yoy) over (
            order by observation_date 
            rows between 2 preceding and current row
        ) as inflation_ma_3m,
        
        avg(unemployment_rate) over (
            order by observation_date 
            rows between 2 preceding and current row
        ) as unemployment_ma_3m,
        
        avg(federal_funds_rate) over (
            order by observation_date 
            rows between 2 preceding and current row
        ) as fed_rate_ma_3m,
        
        -- Month-over-month changes
        lag(inflation_rate_yoy, 1) over (order by observation_date) as inflation_prev_month,
        lag(unemployment_rate, 1) over (order by observation_date) as unemployment_prev_month,
        lag(federal_funds_rate, 1) over (order by observation_date) as fed_rate_prev_month,
        
        current_timestamp as processed_at
        
    from economic_indicators
),

with_classifications as (
    select
        *,
        
        -- Economic regime classification
        case 
            when gdp_growth_rate_yoy > 3 and inflation_rate_yoy < 3 then 'goldilocks'
            when gdp_growth_rate_yoy > 2 and inflation_rate_yoy > 4 then 'overheating'
            when gdp_growth_rate_yoy < 0 and inflation_rate_yoy > 3 then 'stagflation'
            when gdp_growth_rate_yoy < 0 and inflation_rate_yoy < 2 then 'recession'
            when gdp_growth_rate_yoy > 0 and inflation_rate_yoy < 2 then 'recovery'
            else 'transition'
        end as economic_regime,
        
        -- Monetary policy stance
        case 
            when federal_funds_rate - inflation_ma_3m > 2 then 'tight'
            when federal_funds_rate - inflation_ma_3m > 0 then 'neutral'
            when federal_funds_rate - inflation_ma_3m < -2 then 'very_loose'
            else 'loose'
        end as monetary_policy_stance,
        
        -- Labor market health
        case 
            when unemployment_rate < 4 then 'very_strong'
            when unemployment_rate < 5 then 'strong'
            when unemployment_rate < 6 then 'moderate'
            when unemployment_rate < 8 then 'weak'
            else 'very_weak'
        end as labor_market_health,
        
        -- Inflation trend
        case 
            when inflation_rate_yoy - inflation_prev_month > 0.5 then 'accelerating'
            when inflation_rate_yoy - inflation_prev_month < -0.5 then 'decelerating'
            else 'stable'
        end as inflation_trend,
        
        -- Interest rate trend
        case 
            when federal_funds_rate - fed_rate_prev_month > 0.25 then 'hiking'
            when federal_funds_rate - fed_rate_prev_month < -0.25 then 'cutting'
            else 'holding'
        end as rate_trend
        
    from with_trends
)

select * from with_classifications
