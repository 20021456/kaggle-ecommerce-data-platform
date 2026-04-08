-- Fact: Order Items — line-level fact table
select
    i.order_id,
    i.item_seq,
    i.product_id,
    i.seller_id,
    o.purchased_at::date    as order_date,
    o.order_status,
    p.category              as product_category,
    s.state                 as seller_state,
    i.price,
    i.freight_value,
    i.total_item_value
from {{ ref('stg_olist_order_items') }} i
inner join {{ ref('stg_olist_orders') }} o   on i.order_id = o.order_id
left join {{ ref('stg_olist_products') }} p  on i.product_id = p.product_id
left join {{ ref('stg_olist_sellers') }} s   on i.seller_id = s.seller_id
