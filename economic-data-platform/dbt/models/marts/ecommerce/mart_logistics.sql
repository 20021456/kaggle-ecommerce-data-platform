-- Logistics Mart — delivery performance, freight analysis, seller metrics
with order_logistics as (
    select
        o.order_id,
        o.order_date,
        o.order_status,
        o.is_delivered,
        o.days_to_deliver,
        o.delivery_delta_days,
        o.total_freight,
        o.total_order_value,
        o.unique_sellers,
        o.avg_review_score,
        c.state as customer_state
    from {{ ref('fct_orders') }} o
    left join {{ ref('stg_olist_customers') }} c on o.customer_id = c.customer_id
    where o.is_delivered = true
),

-- Daily logistics KPIs
daily_logistics as (
    select
        order_date,
        count(*)                            as delivered_orders,
        avg(days_to_deliver)                as avg_delivery_days,
        percentile_cont(0.5) within group (order by days_to_deliver)
                                            as median_delivery_days,
        percentile_cont(0.95) within group (order by days_to_deliver)
                                            as p95_delivery_days,
        avg(total_freight)                  as avg_freight,
        sum(total_freight)                  as total_freight,

        -- On-time delivery (delivery_delta_days >= 0 means early/on-time)
        sum(case when delivery_delta_days >= 0 then 1 else 0 end)::float
            / nullif(count(*), 0) * 100     as on_time_rate_pct,

        avg(avg_review_score)               as avg_review,

        -- Late deliveries
        sum(case when delivery_delta_days < 0 then 1 else 0 end) as late_deliveries,
        avg(case when delivery_delta_days < 0 then abs(delivery_delta_days) end)
                                            as avg_late_days

    from order_logistics
    group by 1
),

-- By state (customer destination)
by_state as (
    select
        customer_state                      as state,
        count(*)                            as total_deliveries,
        avg(days_to_deliver)                as avg_delivery_days,
        avg(total_freight)                  as avg_freight,
        sum(case when delivery_delta_days >= 0 then 1 else 0 end)::float
            / nullif(count(*), 0) * 100     as on_time_rate_pct,
        avg(avg_review_score)               as avg_review
    from order_logistics
    group by 1
),

-- Seller performance (from intermediate)
sellers as (
    select
        seller_id,
        city                as seller_city,
        state               as seller_state,
        total_orders,
        total_revenue,
        avg_delivery_days   as seller_avg_delivery_days,
        avg_review_score    as seller_avg_review,
        delivery_rate
    from {{ ref('int_seller_performance') }}
)

-- Output: daily logistics + enrichment
select
    dl.order_date,
    dl.delivered_orders,
    dl.avg_delivery_days,
    dl.median_delivery_days,
    dl.p95_delivery_days,
    dl.avg_freight,
    dl.total_freight,
    dl.on_time_rate_pct,
    dl.avg_review,
    dl.late_deliveries,
    dl.avg_late_days,

    -- 7-day moving averages
    avg(dl.avg_delivery_days) over (
        order by dl.order_date rows between 6 preceding and current row
    ) as delivery_days_7d_avg,
    avg(dl.on_time_rate_pct) over (
        order by dl.order_date rows between 6 preceding and current row
    ) as on_time_rate_7d_avg

from daily_logistics dl
order by dl.order_date
