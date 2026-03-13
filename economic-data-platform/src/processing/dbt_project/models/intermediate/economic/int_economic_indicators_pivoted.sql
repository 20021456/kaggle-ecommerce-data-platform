{{
    config(
        materialized='table',
        tags=['economic', 'intermediate', 'time_series']
    )
}}

with fred_data as (
    select * from {{ ref('stg_fred_indicators') }}
),

-- Pivot key indicators into columns for easier analysis
pivoted_indicators as (
    select
        observation_date,
        observation_year,
        observation_month,
        observation_quarter,
        
        -- GDP indicators
        max(case when series_id = 'GDP' then value end) as gdp_current_dollars,
        max(case when series_id = 'GDPC1' then value end) as gdp_real_chained,
        max(case when series_id = 'GDPPOT' then value end) as gdp_potential,
        
        -- Inflation indicators
        max(case when series_id = 'CPIAUCSL' then value end) as cpi_all_urban,
        max(case when series_id = 'CPILFESL' then value end) as cpi_less_food_energy,
        max(case when series_id = 'PCEPI' then value end) as pce_price_index,
        
        -- Employment indicators
        max(case when series_id = 'UNRATE' then value end) as unemployment_rate,
        max(case when series_id = 'PAYEMS' then value end) as nonfarm_payroll,
        max(case when series_id = 'CIVPART' then value end) as labor_force_participation,
        
        -- Interest rate indicators
        max(case when series_id = 'FEDFUNDS' then value end) as federal_funds_rate,
        max(case when series_id = 'DGS10' then value end) as treasury_10y_rate,
        max(case when series_id = 'DGS2' then value end) as treasury_2y_rate,
        max(case when series_id = 'T10Y2Y' then value end) as yield_curve_10y_2y,
        
        -- Money supply indicators
        max(case when series_id = 'M2SL' then value end) as m2_money_supply,
        max(case when series_id = 'M1SL' then value end) as m1_money_supply,
        max(case when series_id = 'BOGMBASE' then value end) as monetary_base,
        
        current_timestamp as processed_at
        
    from fred_data
    group by observation_date, observation_year, observation_month, observation_quarter
),

with_derived_metrics as (
    select
        *,
        
        -- Calculate year-over-year changes
        lag(cpi_all_urban, 12) over (order by observation_date) as cpi_12m_ago,
        case 
            when lag(cpi_all_urban, 12) over (order by observation_date) > 0
            then ((cpi_all_urban - lag(cpi_all_urban, 12) over (order by observation_date)) 
                  / lag(cpi_all_urban, 12) over (order by observation_date)) * 100
            else null
        end as inflation_rate_yoy,
        
        -- GDP growth rate
        lag(gdp_real_chained, 4) over (order by observation_date) as gdp_4q_ago,
        case 
            when lag(gdp_real_chained, 4) over (order by observation_date) > 0
            then ((gdp_real_chained - lag(gdp_real_chained, 4) over (order by observation_date)) 
                  / lag(gdp_real_chained, 4) over (order by observation_date)) * 100
            else null
        end as gdp_growth_rate_yoy,
        
        -- Real interest rate (nominal - inflation)
        federal_funds_rate - 
            case 
                when lag(cpi_all_urban, 12) over (order by observation_date) > 0
                then ((cpi_all_urban - lag(cpi_all_urban, 12) over (order by observation_date)) 
                      / lag(cpi_all_urban, 12) over (order by observation_date)) * 100
                else null
            end as real_interest_rate,
        
        -- Money supply growth
        lag(m2_money_supply, 12) over (order by observation_date) as m2_12m_ago,
        case 
            when lag(m2_money_supply, 12) over (order by observation_date) > 0
            then ((m2_money_supply - lag(m2_money_supply, 12) over (order by observation_date)) 
                  / lag(m2_money_supply, 12) over (order by observation_date)) * 100
            else null
        end as m2_growth_rate_yoy
        
    from pivoted_indicators
)

select * from with_derived_metrics
