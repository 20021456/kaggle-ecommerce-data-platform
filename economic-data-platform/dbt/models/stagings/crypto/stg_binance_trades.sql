{{
    config(
        materialized='view',
        tags=['crypto', 'staging', 'binance']
    )
}}

with source as (
    select * from {{ source('crypto_raw', 'binance_trades') }}
),

cleaned as (
    select
        -- Primary keys
        trade_id,
        symbol,
        
        -- Trade details
        cast(price as decimal(18, 8)) as price,
        cast(quantity as decimal(18, 8)) as quantity,
        cast(price * quantity as decimal(18, 8)) as trade_value_usd,
        
        -- Trade metadata
        is_buyer_maker,
        case 
            when is_buyer_maker then 'sell'
            else 'buy'
        end as trade_side,
        
        -- Timestamps
        cast(trade_time as timestamp) as trade_timestamp,
        date(trade_time) as trade_date,
        cast(ingested_at as timestamp) as ingested_at,
        
        -- Derived fields
        extract(hour from trade_time) as trade_hour,
        extract(dayofweek from trade_time) as trade_day_of_week,
        
        -- Data quality
        case 
            when price > 0 and quantity > 0 then true
            else false
        end as is_valid_trade
        
    from source
    where trade_time is not null
        and price is not null
        and quantity is not null
)

select * from cleaned
where is_valid_trade = true
