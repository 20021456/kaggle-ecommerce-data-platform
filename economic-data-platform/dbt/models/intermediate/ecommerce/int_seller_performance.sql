-- Intermediate: Seller performance metrics
with sellers as (
    select * from {{ ref('stg_olist_sellers') }}
),

items as (
    select * from {{ ref('stg_olist_order_items') }}
),

orders as (
    select order_id, days_to_deliver, is_delivered
    from {{ ref('stg_olist_orders') }}
),

reviews as (
    select order_id, avg(review_score) as avg_score
    from {{ ref('stg_olist_reviews') }}
    group by 1
)

select
    s.seller_id,
    s.city,
    s.state,
    count(distinct i.order_id)              as total_orders,
    count(*)                                as total_items_sold,
    sum(i.price)                            as total_revenue,
    avg(i.price)                            as avg_item_price,
    sum(i.freight_value)                    as total_freight,
    count(distinct i.product_id)            as unique_products,
    avg(o.days_to_deliver)                  as avg_delivery_days,
    avg(r.avg_score)                        as avg_review_score,
    sum(case when o.is_delivered then 1 else 0 end)::float
        / nullif(count(distinct i.order_id), 0) as delivery_rate

from sellers s
inner join items i   on s.seller_id = i.seller_id
left join orders o   on i.order_id = o.order_id
left join reviews r  on i.order_id = r.order_id
group by 1, 2, 3
