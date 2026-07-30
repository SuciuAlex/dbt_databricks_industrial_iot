{{
    config(
        unique_key='event_type_code',
        incremental_strategy='append'
    )
}}

with source as (

    select * from {{ ref('raw_event_types') }}

),

cleaned as (

    select
        event_type_code,
        event_category,
        description,
        cast(has_numeric_payload as boolean) as has_numeric_payload,
        current_timestamp()                  as _loaded_at
    from source
    where event_type_code is not null

)

select * from cleaned
