-- Dimension: Customers with segmentation
with metrics as (
    select * from {{ ref('int_customer_metrics') }}
),

quartiles as (
    select
        percentile_cont(0.25) within group (order by total_spend) as q1,
        percentile_cont(0.50) within group (order by total_spend) as q2,
        percentile_cont(0.75) within group (order by total_spend) as q3
    from metrics
    where total_spend > 0
)

select
    m.customer_unique_id,
    m.city,
    m.state,
    m.order_count,
    m.total_spend,
    m.avg_order_value,
    m.first_order_at,
    m.last_order_at,
    m.avg_review_score,
    m.total_items_bought,
    m.avg_delivery_days,
    m.customer_lifetime_days,
    case
        when m.total_spend >= q.q3 then 'Premium'
        when m.total_spend >= q.q2 then 'Regular'
        when m.total_spend >= q.q1 then 'Basic'
        else 'Low'
    end as customer_segment
from metrics m
cross join quartiles q
