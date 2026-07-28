{{ config(materialized='view') }}

-- GOLD LAYER RULE: this model may only ref() silver models (never bronze or
-- raw directly). See CLAUDE.md section 4.4.

select
    machine_type,
    event_date,
    avg(case when event_type_code = 'SENSOR_TEMPERATURE_READING' then event_value end) as avg_temperature_c,
    avg(case when event_type_code = 'SENSOR_SPEED_READING' then event_value end)       as avg_speed_units_per_min,
    avg(case when event_type_code = 'SENSOR_VIBRATION_READING' then event_value end)   as avg_vibration_mm_s,
    count(case when event_type_code = 'SENSOR_TEMPERATURE_READING' then 1 end)         as temperature_reading_count,
    count(case when event_type_code = 'SENSOR_SPEED_READING' then 1 end)               as speed_reading_count,
    count(case when event_type_code = 'SENSOR_VIBRATION_READING' then 1 end)           as vibration_reading_count
from {{ ref('silver_fact_device_events') }}
where event_type_code in (
    'SENSOR_TEMPERATURE_READING', 'SENSOR_SPEED_READING', 'SENSOR_VIBRATION_READING'
)
group by machine_type, event_date
