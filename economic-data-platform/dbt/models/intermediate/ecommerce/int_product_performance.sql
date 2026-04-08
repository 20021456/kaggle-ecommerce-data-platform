-- Intermediate: Product performance metrics
with products as (
    select * from {{ ref('stg_olist_products') }}
),

items as (
    select * from {{ ref('stg_olist_order_items') }}
),

reviews as (
    select order_id, avg(review_score) as avg_score
    from {{ ref('stg_olist_reviews') }}
    group by 1
),

product_metrics as (
    select
        p.product_id,
        p.category,
        p.weight_g,
        p.volume_cm3,
        count(distinct i.order_id)  as total_orders,
        sum(i.item_seq)             as total_units_sold,
        sum(i.price)                as total_revenue,
        avg(i.price)                as avg_price,
        sum(i.freight_value)        as total_freight_cost,
        count(distinct i.seller_id) as unique_sellers
    from products p
    inner join items i on p.product_id = i.product_id
    group by 1, 2, 3, 4
),

with_reviews as (
    select
        pm.*,
        avg(r.avg_score) as avg_review_score
    from product_metrics pm
    left join items i on pm.product_id = i.product_id
    left join reviews r on i.order_id = r.order_id
    group by pm.product_id, pm.category, pm.weight_g, pm.volume_cm3,
             pm.total_orders, pm.total_units_sold, pm.total_revenue,
             pm.avg_price, pm.total_freight_cost, pm.unique_sellers
)

select * from with_reviews
