-- Dimension: Date spine for all order dates
with date_range as (
    select
        min(purchased_at::date) as min_date,
        max(purchased_at::date) as max_date
    from {{ ref('stg_olist_orders') }}
),

dates as (
    select generate_series(
        (select min_date from date_range),
        (select max_date from date_range),
        '1 day'::interval
    )::date as date_key
)

select
    date_key,
    extract(year from date_key)::int            as year,
    extract(quarter from date_key)::int         as quarter,
    extract(month from date_key)::int           as month,
    to_char(date_key, 'Month')                  as month_name,
    extract(week from date_key)::int            as week_of_year,
    extract(isodow from date_key)::int          as day_of_week,
    to_char(date_key, 'Day')                    as day_name,
    (extract(isodow from date_key) in (6, 7))   as is_weekend,
    to_char(date_key, 'YYYY-Q')                 as year_quarter,
    to_char(date_key, 'YYYY-MM')                as year_month
from dates
