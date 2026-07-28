{{
    config(
        materialized='table'
    )
}}

-- Conformed, business-ready event fact: one row per device event, with
-- machine/event-type attributes joined in and a single generic
-- `event_value` column that lets downstream models (esp. the gold
-- event-frequency views) define "min/max value in a bucket" without
-- needing to know which type-specific payload column applies.

with events as (

    select * from {{ ref('bronze_device_events') }}

),

machines as (

    select
        machine_id,
        machine_type as machine_type_dim,
        plant_location
    from {{ ref('bronze_machines') }}

),

event_types as (

    select
        event_type_code,
        event_category
    from {{ ref('bronze_event_types') }}

)

select
    e.event_id,
    e.machine_id,
    e.machine_type,
    m.plant_location,
    e.event_type_code,
    et.event_category,
    e.event_timestamp,
    e.event_date,
    e.status_value,
    e.temperature_c,
    e.speed_units_per_min,
    e.vibration_mm_s,
    e.product_count,
    e.cycle_duration_seconds,
    e.error_code,
    cast(
        case e.event_type_code
            when 'SENSOR_TEMPERATURE_READING' then e.temperature_c
            when 'SENSOR_SPEED_READING' then e.speed_units_per_min
            when 'SENSOR_VIBRATION_READING' then e.vibration_mm_s
            when 'PRODUCT_COUNT_UPDATE' then e.product_count
            when 'CYCLE_COMPLETE' then e.product_count
            else null
        end as double
    ) as event_value,
    e.source_ingested_at
from events e
inner join machines m on m.machine_id = e.machine_id
left join event_types et on et.event_type_code = e.event_type_code
