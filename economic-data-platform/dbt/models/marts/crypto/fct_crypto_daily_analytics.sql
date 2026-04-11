{{
    config(
        materialized='table',
        tags=['crypto', 'mart', 'analytics']
    )
}}

with crypto_ohlcv as (
    select * from {{ ref('int_crypto_daily_ohlcv') }}
),

coingecko_prices as (
    select * from {{ ref('stg_coingecko_prices') }}
),

-- Enrich OHLCV with market cap and volume data
enriched as (
    select
        o.symbol,
        o.trade_date,
        
        -- OHLCV data
        o.open_price,
        o.high_price,
        o.low_price,
        o.close_price,
        o.avg_price,
        o.total_volume,
        o.total_value_usd,
        o.trade_count,
        
        -- Price changes
        o.price_change,
        o.price_change_percentage,
        o.volatility_percentage,
        
        -- Market metrics from CoinGecko
        c.market_cap_usd,
        c.volume_24h_usd as coingecko_volume_24h,
        c.volume_to_market_cap_ratio,
        
        -- Technical indicators
        o.buy_sell_pressure,
        o.avg_trade_size_usd,
        
        -- Moving averages (7-day, 30-day)
        avg(o.close_price) over (
            partition by o.symbol 
            order by o.trade_date 
            rows between 6 preceding and current row
        ) as ma_7d,
        
        avg(o.close_price) over (
            partition by o.symbol 
            order by o.trade_date 
            rows between 29 preceding and current row
        ) as ma_30d,
        
        -- Volatility (7-day rolling std dev approximation)
        stddev(o.close_price) over (
            partition by o.symbol 
            order by o.trade_date 
            rows between 6 preceding and current row
        ) as volatility_7d,
        
        -- Volume trends
        avg(o.total_value_usd) over (
            partition by o.symbol 
            order by o.trade_date 
            rows between 6 preceding and current row
        ) as avg_volume_7d,
        
        current_timestamp as processed_at
        
    from crypto_ohlcv o
    left join coingecko_prices c
        on o.symbol = concat(c.symbol, 'USDT')
        and o.trade_date = c.price_date
),

with_signals as (
    select
        *,
        
        -- Trend signals
        case 
            when close_price > ma_7d and ma_7d > ma_30d then 'bullish'
            when close_price < ma_7d and ma_7d < ma_30d then 'bearish'
            else 'neutral'
        end as trend_signal,
        
        -- Volume signal
        case 
            when total_value_usd > avg_volume_7d * 1.5 then 'high_volume'
            when total_value_usd < avg_volume_7d * 0.5 then 'low_volume'
            else 'normal_volume'
        end as volume_signal,
        
        -- Volatility signal
        case 
            when volatility_percentage > 5 then 'high_volatility'
            when volatility_percentage < 2 then 'low_volatility'
            else 'normal_volatility'
        end as volatility_signal
        
    from enriched
)

select * from with_signals
