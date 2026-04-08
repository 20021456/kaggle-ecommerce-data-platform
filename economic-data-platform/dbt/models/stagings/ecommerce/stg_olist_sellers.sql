-- Staging: Olist Sellers — standardize geography
with source as (
    select * from {{ source('olist_raw', 'olist_sellers') }}
),

staged as (
    select
        seller_id,
        lpad(seller_zip_code_prefix::text, 5, '0') as zip_code,
        initcap(trim(seller_city))                  as city,
        upper(trim(seller_state))                   as state

    from source
    where seller_id is not null
)

select * from staged
