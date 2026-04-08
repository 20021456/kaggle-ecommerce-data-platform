-- Staging: Olist Customers — standardize geography
with source as (
    select * from {{ source('olist_raw', 'olist_customers') }}
),

staged as (
    select
        customer_id,
        customer_unique_id,
        lpad(customer_zip_code_prefix::text, 5, '0') as zip_code,
        initcap(trim(customer_city))                  as city,
        upper(trim(customer_state))                   as state

    from source
    where customer_id is not null
)

select * from staged
