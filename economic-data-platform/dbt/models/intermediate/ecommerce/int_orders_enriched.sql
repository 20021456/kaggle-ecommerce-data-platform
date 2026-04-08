-- Intermediate: Enriched orders — join items, payments, reviews per order
with orders as (
    select * from {{ ref('stg_olist_orders') }}
),

items_agg as (
    select
        order_id,
        count(*)                    as total_items,
        sum(price)                  as total_product_value,
        sum(freight_value)          as total_freight,
        sum(total_item_value)       as total_order_value,
        count(distinct product_id)  as unique_products,
        count(distinct seller_id)   as unique_sellers
    from {{ ref('stg_olist_order_items') }}
    group by 1
),

payments_agg as (
    select
        order_id,
        count(*)                    as payment_count,
        sum(payment_value)          as total_paid,
        max(payment_type)           as primary_payment_type,
        max(installments)           as max_installments
    from {{ ref('stg_olist_payments') }}
    group by 1
),

reviews_agg as (
    select
        order_id,
        avg(review_score)           as avg_review_score,
        count(*)                    as review_count,
        bool_or(has_comment)        as has_review_comment
    from {{ ref('stg_olist_reviews') }}
    group by 1
)

select
    o.*,
    coalesce(i.total_items, 0)          as total_items,
    coalesce(i.total_product_value, 0)  as total_product_value,
    coalesce(i.total_freight, 0)        as total_freight,
    coalesce(i.total_order_value, 0)    as total_order_value,
    coalesce(i.unique_products, 0)      as unique_products,
    coalesce(i.unique_sellers, 0)       as unique_sellers,
    coalesce(p.payment_count, 0)        as payment_count,
    coalesce(p.total_paid, 0)           as total_paid,
    p.primary_payment_type,
    p.max_installments,
    r.avg_review_score,
    coalesce(r.review_count, 0)         as review_count,
    coalesce(r.has_review_comment, false) as has_review_comment

from orders o
left join items_agg    i on o.order_id = i.order_id
left join payments_agg p on o.order_id = p.order_id
left join reviews_agg  r on o.order_id = r.order_id
