{{
    config(
        materialized='view',
        tags=['crypto', 'staging', 'coingecko']
    )
}}

with source as (
    select * from {{ source('crypto_raw', 'coingecko_prices') }}
),

cleaned as (
    select
        -- Primary keys
        coin_id,
        symbol,
        name,
        
        -- Price metrics
        cast(current_price as decimal(18, 8)) as current_price_usd,
        cast(market_cap as decimal(20, 2)) as market_cap_usd,
        cast(total_volume as decimal(20, 2)) as volume_24h_usd,
        
        -- Price changes
        cast(price_change_24h as decimal(18, 8)) as price_change_24h_usd,
        cast(price_change_percentage_24h as decimal(10, 4)) as price_change_percentage_24h,
        
        -- Timestamps
        cast(last_updated as timestamp) as last_updated_at,
        date(last_updated) as price_date,
        cast(ingested_at as timestamp) as ingested_at,
        
        -- Derived fields
        case 
            when market_cap > 0 then cast(total_volume as decimal(20, 2)) / cast(market_cap as decimal(20, 2))
            else null
        end as volume_to_market_cap_ratio,
        
        case
            when price_change_percentage_24h > 0 then 'up'
            when price_change_percentage_24h < 0 then 'down'
            else 'flat'
        end as price_trend_24h,
        
        -- Data quality
        case 
            when current_price > 0 and market_cap > 0 then true
            else false
        end as is_valid_price
        
    from source
    where last_updated is not null
        and coin_id is not null
)

select * from cleaned
where is_valid_price = true
