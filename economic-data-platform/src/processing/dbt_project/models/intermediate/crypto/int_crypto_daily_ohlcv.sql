{{
    config(
        materialized='table',
        tags=['crypto', 'intermediate', 'aggregated']
    )
}}

with binance_trades as (
    select * from {{ ref('stg_binance_trades') }}
),

daily_aggregates as (
    select
        symbol,
        trade_date,
        
        -- Price metrics
        min(price) as low_price,
        max(price) as high_price,
        first_value(price) over (partition by symbol, trade_date order by trade_timestamp) as open_price,
        last_value(price) over (partition by symbol, trade_date order by trade_timestamp) as close_price,
        avg(price) as avg_price,
        
        -- Volume metrics
        sum(quantity) as total_volume,
        sum(trade_value_usd) as total_value_usd,
        count(*) as trade_count,
        
        -- Trade side analysis
        sum(case when trade_side = 'buy' then trade_value_usd else 0 end) as buy_volume_usd,
        sum(case when trade_side = 'sell' then trade_value_usd else 0 end) as sell_volume_usd,
        
        -- Timestamps
        min(trade_timestamp) as first_trade_at,
        max(trade_timestamp) as last_trade_at,
        current_timestamp as processed_at
        
    from binance_trades
    group by symbol, trade_date
),

with_derived_metrics as (
    select
        *,
        
        -- Price change metrics
        close_price - open_price as price_change,
        case 
            when open_price > 0 then ((close_price - open_price) / open_price) * 100
            else null
        end as price_change_percentage,
        
        -- Volatility
        high_price - low_price as price_range,
        case 
            when avg_price > 0 then ((high_price - low_price) / avg_price) * 100
            else null
        end as volatility_percentage,
        
        -- Buy/Sell pressure
        case 
            when (buy_volume_usd + sell_volume_usd) > 0 
            then (buy_volume_usd - sell_volume_usd) / (buy_volume_usd + sell_volume_usd)
            else 0
        end as buy_sell_pressure,
        
        -- Average trade size
        case 
            when trade_count > 0 then total_value_usd / trade_count
            else null
        end as avg_trade_size_usd
        
    from daily_aggregates
)

select * from with_derived_metrics
