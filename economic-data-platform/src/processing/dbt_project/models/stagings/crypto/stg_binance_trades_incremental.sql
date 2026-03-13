"""
Incremental Model with CDC Logic
Example: Incremental loading with checkpoints
"""

{{
    config(
        materialized='incremental',
        unique_key='trade_id',
        incremental_strategy='merge',
        on_schema_change='append_new_columns',
        tags=['crypto', 'staging', 'incremental']
    )
}}

with source as (
    select * from {{ source('crypto_raw', 'binance_trades') }}
    
    {% if is_incremental() %}
    -- Only load new data since last run
    where ingested_at > (select max(ingested_at) from {{ this }})
    {% endif %}
),

cleaned as (
    select
        trade_id,
        symbol,
        cast(price as decimal(18, 8)) as price,
        cast(quantity as decimal(18, 8)) as quantity,
        cast(price * quantity as decimal(18, 8)) as trade_value_usd,
        is_buyer_maker,
        case when is_buyer_maker then 'sell' else 'buy' end as trade_side,
        cast(trade_time as timestamp) as trade_timestamp,
        date(trade_time) as trade_date,
        cast(ingested_at as timestamp) as ingested_at,
        extract(hour from trade_time) as trade_hour,
        case when price > 0 and quantity > 0 then true else false end as is_valid_trade,
        
        -- CDC metadata
        current_timestamp as dbt_updated_at,
        '{{ invocation_id }}' as dbt_invocation_id
        
    from source
    where trade_time is not null
        and price is not null
        and quantity is not null
)

select * from cleaned
where is_valid_trade = true
