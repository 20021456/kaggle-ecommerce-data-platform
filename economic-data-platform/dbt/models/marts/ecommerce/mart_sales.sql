-- Sales Mart — daily/monthly revenue, category, payment analysis
-- Materialized as table in gold_ecommerce schema
with daily_orders as (
    select
        order_date,
        count(*)                                    as order_count,
        sum(total_order_value)                      as gross_revenue,
        sum(total_freight)                          as total_freight,
        sum(total_product_value)                    as net_revenue,
        avg(total_order_value)                      as avg_order_value,
        sum(total_items)                            as items_sold,
        count(distinct customer_unique_id)          as unique_customers,
        avg(avg_review_score)                       as avg_review,
        sum(case when is_canceled then 1 else 0 end) as canceled_orders
    from {{ ref('fct_orders') }}
    group by 1
),

by_category as (
    select
        order_date,
        product_category,
        count(*)                as items_sold,
        sum(total_item_value)   as category_revenue,
        avg(price)              as avg_price
    from {{ ref('fct_order_items') }}
    where product_category is not null
    group by 1, 2
),

top_category_per_day as (
    select distinct on (order_date)
        order_date,
        product_category as top_category,
        category_revenue as top_category_revenue
    from by_category
    order by order_date, category_revenue desc
),

by_payment as (
    select
        o.order_date,
        p.payment_type,
        count(*)                as payment_count,
        sum(p.payment_value)    as payment_total
    from {{ ref('fct_orders') }} o
    inner join {{ ref('stg_olist_payments') }} p on o.order_id = p.order_id
    group by 1, 2
),

top_payment_per_day as (
    select distinct on (order_date)
        order_date,
        payment_type as top_payment_type,
        payment_total as top_payment_total
    from by_payment
    order by order_date, payment_total desc
)

select
    d.order_date,

    -- Revenue metrics
    d.order_count,
    d.gross_revenue,
    d.net_revenue,
    d.total_freight,
    d.avg_order_value,
    d.items_sold,
    d.unique_customers,
    d.avg_review,
    d.canceled_orders,

    -- Cancellation rate
    round(d.canceled_orders::numeric / nullif(d.order_count, 0) * 100, 2)
        as cancellation_rate_pct,

    -- Top category
    tc.top_category,
    tc.top_category_revenue,

    -- Top payment method
    tp.top_payment_type,
    tp.top_payment_total,

    -- Running totals
    sum(d.gross_revenue) over (order by d.order_date) as cumulative_revenue,
    sum(d.order_count)   over (order by d.order_date) as cumulative_orders,

    -- 7-day moving averages
    avg(d.gross_revenue) over (
        order by d.order_date rows between 6 preceding and current row
    ) as revenue_7d_avg,
    avg(d.order_count) over (
        order by d.order_date rows between 6 preceding and current row
    ) as orders_7d_avg

from daily_orders d
left join top_category_per_day tc on d.order_date = tc.order_date
left join top_payment_per_day tp  on d.order_date = tp.order_date
order by d.order_date
