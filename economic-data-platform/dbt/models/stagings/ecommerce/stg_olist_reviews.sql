-- Staging: Olist Reviews — cast score, compute response time
with source as (
    select * from {{ source('olist_raw', 'olist_reviews') }}
),

staged as (
    select
        review_id,
        order_id,
        review_score::int                           as review_score,
        nullif(trim(review_comment_title), '')      as comment_title,
        nullif(trim(review_comment_message), '')    as comment_message,
        review_creation_date::timestamp             as created_at,
        review_answer_timestamp::timestamp          as answered_at,

        -- Derived
        (review_comment_message is not null and trim(review_comment_message) != '')::boolean
            as has_comment,

        extract(epoch from (
            review_answer_timestamp::timestamp - review_creation_date::timestamp
        )) / 3600.0 as response_time_hours

    from source
    where review_id is not null
)

select * from staged
