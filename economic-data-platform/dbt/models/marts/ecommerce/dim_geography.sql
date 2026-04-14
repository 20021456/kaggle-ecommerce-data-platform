-- Dimension: Geography — unique zip_code → city → state mapping
-- Source: olist_customers + olist_sellers + olist_geolocation
-- Grain: one row per zip_code_prefix

with customer_geo as (
    select distinct
        customer_zip_code_prefix as zip_code_prefix,
        customer_city            as city,
        customer_state           as state
    from {{ source('olist_raw', 'olist_customers') }}
    where customer_zip_code_prefix is not null
),

seller_geo as (
    select distinct
        seller_zip_code_prefix as zip_code_prefix,
        seller_city            as city,
        seller_state           as state
    from {{ source('olist_raw', 'olist_sellers') }}
    where seller_zip_code_prefix is not null
),

geolocation as (
    select
        geolocation_zip_code_prefix as zip_code_prefix,
        avg(geolocation_lat)        as latitude,
        avg(geolocation_lng)        as longitude,
        max(geolocation_city)       as city,
        max(geolocation_state)      as state
    from {{ source('olist_raw', 'olist_geolocation') }}
    where geolocation_zip_code_prefix is not null
    group by 1
),

combined as (
    select zip_code_prefix, city, state from customer_geo
    union
    select zip_code_prefix, city, state from seller_geo
),

deduped as (
    select
        zip_code_prefix,
        max(city)  as city,
        max(state) as state
    from combined
    group by 1
)

select
    d.zip_code_prefix,
    d.city,
    d.state,
    -- Region mapping (Brazilian macro-regions)
    case d.state
        when 'SP' then 'Sudeste'
        when 'RJ' then 'Sudeste'
        when 'MG' then 'Sudeste'
        when 'ES' then 'Sudeste'
        when 'PR' then 'Sul'
        when 'SC' then 'Sul'
        when 'RS' then 'Sul'
        when 'BA' then 'Nordeste'
        when 'PE' then 'Nordeste'
        when 'CE' then 'Nordeste'
        when 'MA' then 'Nordeste'
        when 'PB' then 'Nordeste'
        when 'RN' then 'Nordeste'
        when 'AL' then 'Nordeste'
        when 'SE' then 'Nordeste'
        when 'PI' then 'Nordeste'
        when 'DF' then 'Centro-Oeste'
        when 'GO' then 'Centro-Oeste'
        when 'MT' then 'Centro-Oeste'
        when 'MS' then 'Centro-Oeste'
        when 'AM' then 'Norte'
        when 'PA' then 'Norte'
        when 'AC' then 'Norte'
        when 'RO' then 'Norte'
        when 'RR' then 'Norte'
        when 'AP' then 'Norte'
        when 'TO' then 'Norte'
        else 'Desconhecido'
    end as region,
    g.latitude,
    g.longitude
from deduped d
left join geolocation g on g.zip_code_prefix = d.zip_code_prefix
