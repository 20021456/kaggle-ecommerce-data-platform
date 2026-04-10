-- Logistics by State — geographic delivery performance
with order_logistics as (
    select
        o.order_id,
        o.days_to_deliver,
        o.delivery_delta_days,
        o.total_freight,
        o.total_order_value,
        o.avg_review_score,
        c.state as customer_state
    from {{ ref('fct_orders') }} o
    left join {{ ref('stg_olist_customers') }} c on o.customer_id = c.customer_id
    where o.is_delivered = true
)

select
    customer_state                          as state,
    count(*)                                as total_deliveries,
    round(avg(days_to_deliver)::numeric, 1) as avg_delivery_days,
    round(avg(total_freight)::numeric, 2)   as avg_freight,
    round((sum(case when delivery_delta_days >= 0 then 1 else 0 end)::numeric
        / nullif(count(*), 0) * 100), 1)    as on_time_rate_pct,
    round(avg(avg_review_score)::numeric, 2) as avg_review,
    round(avg(total_order_value)::numeric, 2) as avg_order_value,
    sum(total_freight)                       as total_freight_revenue
from order_logistics
where customer_state is not null
group by 1
order by total_deliveries desc
