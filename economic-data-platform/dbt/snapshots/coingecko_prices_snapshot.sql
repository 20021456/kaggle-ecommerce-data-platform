"""
Snapshot Configuration for SCD Type 2
Tracks historical changes in cryptocurrency prices
"""

{% snapshot coingecko_prices_snapshot %}

{{
    config(
      target_schema='snapshots',
      unique_key='coin_id',
      strategy='timestamp',
      updated_at='last_updated',
      invalidate_hard_deletes=True,
      tags=['crypto', 'snapshot', 'scd2']
    )
}}

select
    coin_id,
    symbol,
    name,
    current_price as price_usd,
    market_cap as market_cap_usd,
    total_volume as volume_24h_usd,
    price_change_24h,
    price_change_percentage_24h,
    last_updated,
    ingested_at
from {{ source('crypto_raw', 'coingecko_prices') }}

{% endsnapshot %}
