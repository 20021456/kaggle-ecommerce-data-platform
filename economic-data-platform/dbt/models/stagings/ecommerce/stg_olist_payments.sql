-- Staging: Olist Payments — cast types
with source as (
    select * from {{ source('olist_raw', 'olist_payments') }}
),

staged as (
    select
        order_id,
        payment_sequential::int         as payment_seq,
        trim(lower(payment_type))       as payment_type,
        payment_installments::int       as installments,
        payment_value::numeric(10,2)    as payment_value

    from source
    where order_id is not null
)

select * from staged
