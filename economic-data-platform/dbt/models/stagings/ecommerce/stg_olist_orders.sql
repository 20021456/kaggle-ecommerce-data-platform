-- Staging: Olist Orders — clean timestamps, add delivery metrics
with source as (
    select * from {{ source('olist_raw', 'olist_orders') }}
),

staged as (
    select
        order_id,
        customer_id,
        trim(lower(order_status)) as order_status,

        order_purchase_timestamp::timestamp   as purchased_at,
        order_approved_at::timestamp          as approved_at,
        order_delivered_carrier_date::timestamp as shipped_at,
        order_delivered_customer_date::timestamp as delivered_at,
        order_estimated_delivery_date::timestamp as estimated_delivery_at,

        -- Derived
        (order_status = 'delivered')::boolean as is_delivered,
        (order_status = 'canceled')::boolean  as is_canceled,

        extract(epoch from (
            order_delivered_customer_date::timestamp - order_purchase_timestamp::timestamp
        )) / 86400.0 as days_to_deliver,

        extract(epoch from (
            order_approved_at::timestamp - order_purchase_timestamp::timestamp
        )) / 3600.0 as hours_to_approve,

        extract(epoch from (
            order_estimated_delivery_date::timestamp - order_delivered_customer_date::timestamp
        )) / 86400.0 as delivery_delta_days  -- positive = early, negative = late

    from source
    where order_id is not null
)

select * from staged
