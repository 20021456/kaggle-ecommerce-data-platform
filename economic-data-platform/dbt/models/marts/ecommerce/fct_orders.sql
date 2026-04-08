-- Fact: Orders — central fact table
select
    o.order_id,
    o.customer_id,
    c.customer_unique_id,
    o.purchased_at::date                    as order_date,
    o.order_status,
    o.is_delivered,
    o.is_canceled,
    o.days_to_deliver,
    o.delivery_delta_days,
    o.total_items,
    o.total_product_value,
    o.total_freight,
    o.total_order_value,
    o.total_paid,
    o.unique_products,
    o.unique_sellers,
    o.primary_payment_type,
    o.max_installments,
    o.avg_review_score,
    o.review_count,
    o.has_review_comment
from {{ ref('int_orders_enriched') }} o
left join {{ ref('stg_olist_customers') }} c
    on o.customer_id = c.customer_id
