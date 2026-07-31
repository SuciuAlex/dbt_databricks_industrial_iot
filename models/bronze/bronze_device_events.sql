{{
    config(
        incremental_strategy='append'
    )
}}

-- BRONZE LAYER RULE (CLAUDE.md section 4.2): bronze is an append-only landing
-- zone. It types and stamps the incoming batch and nothing else — no
-- deduplication and no quarantining, so this table legitimately contains
-- duplicate event_ids and null machine_ids. Silver resolves both.
--
-- var('load_date') selects one simulated daily gateway load (e.g.
-- `dbt build --select bronze_device_events --vars 'load_date: 2026-04-02'`).
-- Unset, every batch is appended. Re-running the same load_date appends its
-- rows a second time; that duplication is intentional and is what silver's
-- dedup step absorbs.

with source as (

    select * from {{ ref('raw_device_events') }}

),

cleaned as (

    select
        event_id,
        machine_id,
        machine_type,
        event_type_code,
        cast(event_timestamp as timestamp)     as event_timestamp,
        cast(event_date as date)               as event_date,
        status_value,
        cast(temperature_c as double)          as temperature_c,
        cast(speed_units_per_min as double)    as speed_units_per_min,
        cast(vibration_mm_s as double)         as vibration_mm_s,
        cast(product_count as bigint)          as product_count,
        cast(cycle_duration_seconds as bigint) as cycle_duration_seconds,
        error_code,
        cast(source_ingested_at as timestamp)  as source_ingested_at,
        cast(load_date as date)                as load_date,
        {{ dbt.current_timestamp() }}          as _loaded_at
    from source

)

select * from cleaned

{% if var('load_date', '') %}
where load_date = cast('{{ var('load_date') }}' as date)
{% endif %}
