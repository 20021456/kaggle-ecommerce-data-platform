-- Staging: Olist Order Items — cast numerics, compute total
with source as (
    select * from {{ source('olist_raw', 'olist_order_items') }}
),

staged as (
    select
        order_id,
        order_item_id::int              as item_seq,
        product_id,
        seller_id,
        shipping_limit_date::timestamp  as shipping_limit_at,
        price::numeric(10,2)            as price,
        freight_value::numeric(10,2)    as freight_value,

        (price::numeric(10,2) + freight_value::numeric(10,2)) as total_item_value

    from source
    where order_id is not null
)

select * from staged
