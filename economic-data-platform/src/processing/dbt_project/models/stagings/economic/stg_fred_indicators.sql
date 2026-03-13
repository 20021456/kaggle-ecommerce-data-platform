{{
    config(
        materialized='view',
        tags=['economic', 'staging', 'fred']
    )
}}

with source as (
    select * from {{ source('economic_raw', 'fred_series') }}
),

cleaned as (
    select
        -- Primary keys
        series_id,
        cast(date as date) as observation_date,
        
        -- Series metadata
        series_title,
        series_units,
        series_frequency,
        
        -- Value
        cast(value as decimal(20, 4)) as value,
        
        -- Timestamps
        cast(ingested_at as timestamp) as ingested_at,
        
        -- Derived fields
        extract(year from date) as observation_year,
        extract(month from date) as observation_month,
        extract(quarter from date) as observation_quarter,
        
        -- Categorization
        case 
            when series_id in ('GDP', 'GDPC1', 'GDPPOT') then 'gdp'
            when series_id in ('CPIAUCSL', 'CPILFESL', 'PCEPI') then 'inflation'
            when series_id in ('UNRATE', 'PAYEMS', 'CIVPART') then 'employment'
            when series_id in ('FEDFUNDS', 'DGS10', 'DGS2', 'T10Y2Y') then 'interest_rates'
            when series_id in ('M2SL', 'M1SL', 'BOGMBASE') then 'money_supply'
            else 'other'
        end as indicator_category,
        
        -- Data quality
        case 
            when value is not null and date is not null then true
            else false
        end as is_valid_observation
        
    from source
    where date is not null
        and series_id is not null
)

select * from cleaned
where is_valid_observation = true
