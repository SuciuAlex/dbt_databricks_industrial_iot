{{
    config(
        unique_key='event_id',
        incremental_strategy='merge'
    )
}}

with source as (

    select * from {{ ref('raw_device_events') }}

),

filtered as (

    -- Quarantine rows with a null machine_id (simulated malformed gateway
    -- payloads, injected intentionally in raw_device_events) — dropping them
    -- here is what makes the not_null test on this model's machine_id pass
    -- because of the transformation, not by accident.
    select *
    from source
    where machine_id is not null

),

deduplicated as (

    -- The raw seed intentionally contains a small number of duplicate
    -- event_ids (simulated re-delivery). Keep the latest-ingested copy.
    select *
    from filtered
    qualify row_number() over (
        partition by event_id
        order by source_ingested_at desc
    ) = 1

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
        current_timestamp()                    as _loaded_at
    from deduplicated

)

select * from cleaned

{% if is_incremental() %}
where event_timestamp > (select coalesce(max(event_timestamp), timestamp('1900-01-01')) from {{ this }})
{% endif %}
