-- Dimension: Products with performance stats
select
    product_id,
    category,
    weight_g,
    volume_cm3,
    total_orders,
    total_units_sold,
    total_revenue,
    avg_price,
    total_freight_cost,
    unique_sellers,
    avg_review_score
from {{ ref('int_product_performance') }}
