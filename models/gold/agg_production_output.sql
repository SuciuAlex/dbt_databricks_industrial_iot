{{ config(materialized='view') }}

-- GOLD LAYER RULE: this model may only ref() silver models (never bronze or
-- raw directly). See CLAUDE.md section 4.4.

select
    machine_id,
    machine_type,
    event_date,
    sum(case when event_type_code = 'PRODUCT_COUNT_UPDATE' then product_count else 0 end) as total_product_count,
    count(case when event_type_code = 'CYCLE_START' then 1 end)                            as cycle_start_count,
    count(case when event_type_code = 'CYCLE_COMPLETE' then 1 end)                         as cycle_complete_count,
    sum(case when event_type_code = 'CYCLE_COMPLETE' then product_count else 0 end)        as cycle_product_count,
    avg(case when event_type_code = 'CYCLE_COMPLETE' then cycle_duration_seconds end)      as avg_cycle_duration_seconds
from {{ ref('silver_fact_device_events') }}
group by machine_id, machine_type, event_date
