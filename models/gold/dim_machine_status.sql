{{ config(materialized='view') }}

-- GOLD LAYER RULE: this model may only ref() silver models (never bronze or
-- raw directly). See CLAUDE.md section 4.4.
--
-- Active-row slice of the silver_dim_machines SCD2 dimension, joined with
-- each machine's latest sensor reading. See dim_machine_status_history for
-- the full historical trail.

with current_machines as (

    select *
    from {{ ref('silver_dim_machines') }}
    where is_current = true

),

latest_sensor_reading as (

    select
        machine_id,
        event_type_code,
        event_value,
        event_timestamp,
        row_number() over (
            partition by machine_id, event_type_code
            order by event_timestamp desc
        ) as rn
    from {{ ref('silver_fact_device_events') }}
    where event_type_code in (
        'SENSOR_TEMPERATURE_READING', 'SENSOR_SPEED_READING', 'SENSOR_VIBRATION_READING'
    )

),

latest_temperature as (
    select machine_id, event_value as latest_temperature_c, event_timestamp as latest_temperature_at
    from latest_sensor_reading
    where event_type_code = 'SENSOR_TEMPERATURE_READING' and rn = 1
),

latest_speed as (
    select machine_id, event_value as latest_speed_units_per_min, event_timestamp as latest_speed_at
    from latest_sensor_reading
    where event_type_code = 'SENSOR_SPEED_READING' and rn = 1
),

latest_vibration as (
    select machine_id, event_value as latest_vibration_mm_s, event_timestamp as latest_vibration_at
    from latest_sensor_reading
    where event_type_code = 'SENSOR_VIBRATION_READING' and rn = 1
)

select
    cm.machine_id,
    cm.machine_type,
    cm.status_value,
    cm.plant_location,
    cm.firmware_version,
    cm.valid_from as status_since,
    lt.latest_temperature_c,
    lt.latest_temperature_at,
    ls.latest_speed_units_per_min,
    ls.latest_speed_at,
    lv.latest_vibration_mm_s,
    lv.latest_vibration_at
from current_machines cm
left join latest_temperature lt on lt.machine_id = cm.machine_id
left join latest_speed ls on ls.machine_id = cm.machine_id
left join latest_vibration lv on lv.machine_id = cm.machine_id
