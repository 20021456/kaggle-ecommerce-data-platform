-- Intermediate: Customer-level metrics
with customers as (
    select * from {{ ref('stg_olist_customers') }}
),

orders as (
    select * from {{ ref('int_orders_enriched') }}
),

customer_orders as (
    select
        c.customer_unique_id,
        min(c.city)                     as city,
        min(c.state)                    as state,
        count(distinct o.order_id)      as order_count,
        sum(o.total_order_value)        as total_spend,
        avg(o.total_order_value)        as avg_order_value,
        min(o.purchased_at)             as first_order_at,
        max(o.purchased_at)             as last_order_at,
        avg(o.avg_review_score)         as avg_review_score,
        sum(o.total_items)              as total_items_bought,
        avg(o.days_to_deliver)          as avg_delivery_days

    from customers c
    inner join orders o on c.customer_id = o.customer_id
    group by 1
)

select
    *,
    extract(epoch from (last_order_at - first_order_at)) / 86400.0 as customer_lifetime_days
from customer_orders
