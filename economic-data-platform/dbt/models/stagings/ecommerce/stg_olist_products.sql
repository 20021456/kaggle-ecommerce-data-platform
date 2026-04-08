-- Staging: Olist Products — English categories, volume calc
with source as (
    select * from {{ source('olist_raw', 'olist_products') }}
),

translation as (
    select * from {{ source('olist_raw', 'olist_category_translation') }}
),

staged as (
    select
        p.product_id,
        p.product_category_name           as category_pt,
        coalesce(t.product_category_name_english, p.product_category_name)
                                          as category,
        p.product_name_lenght::int        as name_length,
        p.product_description_lenght::int as description_length,
        p.product_photos_qty::int         as photos_qty,
        p.product_weight_g::int           as weight_g,
        p.product_length_cm::int          as length_cm,
        p.product_height_cm::int          as height_cm,
        p.product_width_cm::int           as width_cm,

        -- Derived
        (p.product_length_cm::int * p.product_height_cm::int * p.product_width_cm::int)
            as volume_cm3

    from source p
    left join translation t
        on p.product_category_name = t.product_category_name
    where p.product_id is not null
)

select * from staged
