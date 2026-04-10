-- Customer Mart — RFM segmentation, LTV, churn indicators
with base as (
    select * from {{ ref('dim_customers') }}
),

rfm_scores as (
    select
        *,
        -- Recency: days since last order (lower = better → higher score)
        ntile(5) over (order by last_order_at desc)  as recency_score,
        -- Frequency: order count (higher = better)
        ntile(5) over (order by order_count asc)      as frequency_score,
        -- Monetary: total spend (higher = better)
        ntile(5) over (order by total_spend asc)       as monetary_score
    from base
    where order_count > 0
),

with_rfm as (
    select
        *,
        recency_score + frequency_score + monetary_score as rfm_total,
        recency_score::text || frequency_score::text || monetary_score::text as rfm_code,

        case
            when recency_score >= 4 and frequency_score >= 4 and monetary_score >= 4
                then 'Champions'
            when recency_score >= 3 and frequency_score >= 3 and monetary_score >= 3
                then 'Loyal Customers'
            when recency_score >= 4 and frequency_score <= 2
                then 'New Customers'
            when recency_score >= 3 and monetary_score >= 3
                then 'Potential Loyalists'
            when recency_score <= 2 and frequency_score >= 3 and monetary_score >= 3
                then 'At Risk'
            when recency_score <= 2 and frequency_score >= 4
                then 'Cannot Lose Them'
            when recency_score <= 2 and frequency_score <= 2 and monetary_score <= 2
                then 'Lost'
            else 'Others'
        end as rfm_segment
    from rfm_scores
)

select
    customer_unique_id,
    city,
    state,
    customer_segment,    -- from dim_customers (spend quartile)

    -- Order metrics
    order_count,
    total_spend,
    avg_order_value,
    total_items_bought,
    first_order_at,
    last_order_at,
    customer_lifetime_days,

    -- Satisfaction
    avg_review_score,
    avg_delivery_days,

    -- RFM
    recency_score,
    frequency_score,
    monetary_score,
    rfm_total,
    rfm_code,
    rfm_segment,

    -- LTV proxy (avg_order_value * predicted_annual_orders)
    case
        when customer_lifetime_days > 0
        then round((total_spend / nullif(customer_lifetime_days, 0) * 365)::numeric, 2)
        else total_spend
    end as estimated_annual_value,

    -- Churn indicator
    case
        when last_order_at < (select max(last_order_at) from base) - interval '90 days'
        then true else false
    end as is_churned

from with_rfm
