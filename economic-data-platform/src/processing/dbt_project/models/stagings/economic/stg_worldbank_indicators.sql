{{
    config(
        materialized='view',
        tags=['economic', 'staging', 'worldbank']
    )
}}

with source as (
    select * from {{ source('economic_raw', 'worldbank_indicators') }}
),

cleaned as (
    select
        -- Primary keys
        country_code,
        country_name,
        indicator_code,
        indicator_name,
        cast(year as integer) as year,
        
        -- Value
        cast(value as decimal(20, 4)) as value,
        
        -- Timestamps
        cast(ingested_at as timestamp) as ingested_at,
        
        -- Derived fields
        case 
            when country_code in ('USA', 'CHN', 'JPN', 'DEU', 'GBR', 'FRA', 'IND', 'ITA', 'BRA', 'CAN') 
            then 'major_economy'
            else 'other'
        end as economy_classification,
        
        -- Categorization
        case 
            when indicator_code like 'NY.GDP%' then 'gdp'
            when indicator_code like 'FP.CPI%' then 'inflation'
            when indicator_code like 'SL.UEM%' then 'unemployment'
            when indicator_code like 'NE.TRD%' then 'trade'
            when indicator_code like 'SP.POP%' then 'population'
            else 'other'
        end as indicator_category,
        
        -- Data quality
        case 
            when value is not null and year is not null then true
            else false
        end as is_valid_observation
        
    from source
    where year is not null
        and country_code is not null
        and indicator_code is not null
)

select * from cleaned
where is_valid_observation = true
