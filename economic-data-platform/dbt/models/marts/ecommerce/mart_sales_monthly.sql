-- Monthly Sales Summary — for dashboard trend charts
with monthly as (
    select
        date_trunc('month', order_date)::date   as month,
        count(*)                                 as order_count,
        sum(total_order_value)                   as gross_revenue,
        sum(total_product_value)                 as net_revenue,
        sum(total_freight)                       as freight_revenue,
        avg(total_order_value)                   as avg_order_value,
        sum(total_items)                         as items_sold,
        count(distinct customer_unique_id)       as unique_customers,
        avg(avg_review_score)                    as avg_review,
        sum(case when is_canceled then 1 else 0 end) as canceled_orders
    from {{ ref('fct_orders') }}
    group by 1
)

select
    month,
    to_char(month, 'YYYY-MM')   as year_month,
    order_count,
    gross_revenue,
    net_revenue,
    freight_revenue,
    avg_order_value,
    items_sold,
    unique_customers,
    avg_review,
    canceled_orders,

    -- Month-over-month growth
    round((gross_revenue - lag(gross_revenue) over (order by month))
        / nullif(lag(gross_revenue) over (order by month), 0) * 100, 1)
        as revenue_mom_pct,
    round((order_count - lag(order_count) over (order by month))::numeric
        / nullif(lag(order_count) over (order by month), 0) * 100, 1)
        as orders_mom_pct

from monthly
order by month
