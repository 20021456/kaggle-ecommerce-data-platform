-- Dimension: Sellers with performance stats
select
    seller_id,
    city,
    state,
    total_orders,
    total_items_sold,
    total_revenue,
    avg_item_price,
    unique_products,
    avg_delivery_days,
    avg_review_score,
    delivery_rate
from {{ ref('int_seller_performance') }}
