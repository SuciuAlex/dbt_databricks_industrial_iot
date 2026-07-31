{{
    config(
        incremental_strategy='append'
    )
}}

-- BRONZE LAYER RULE (CLAUDE.md section 4.2): append-only landing zone. Every
-- run re-appends the reference seed, so duplicate error_code rows are expected
-- here; the silver models deduplicate before joining.

with source as (

    select * from {{ ref('raw_error_codes') }}

),

cleaned as (

    select
        error_code,
        severity,
        description,
        cast(requires_maintenance as boolean) as requires_maintenance,
        {{ dbt.current_timestamp() }}         as _loaded_at
    from source

)

select * from cleaned
