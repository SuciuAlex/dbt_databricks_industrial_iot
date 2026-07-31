{{
    config(
        incremental_strategy='append'
    )
}}

-- BRONZE LAYER RULE (CLAUDE.md section 4.2): append-only landing zone. Every
-- run re-appends the reference seed, so duplicate event_type_code rows are
-- expected here; the silver models deduplicate before joining.

with source as (

    select * from {{ ref('raw_event_types') }}

),

cleaned as (

    select
        event_type_code,
        event_category,
        description,
        cast(has_numeric_payload as boolean) as has_numeric_payload,
        {{ dbt.current_timestamp() }}        as _loaded_at
    from source

)

select * from cleaned
