{{ config(materialized='view') }}

-- GOLD LAYER RULE: this model may only ref() silver models (never bronze or
-- raw directly). See CLAUDE.md section 4.4.

with error_events as (

    select * from {{ ref('silver_fact_error_events') }}

),

machines as (

    select distinct machine_id, machine_type
    from {{ ref('silver_dim_machines') }}

)

select
    m.machine_type,
    ee.severity,
    count(*)                                                           as error_count,
    avg(ee.resolution_time_seconds)                                    as avg_resolution_time_seconds,
    sum(case when ee.requires_maintenance then 1 else 0 end)           as maintenance_required_count
from error_events ee
inner join machines m on m.machine_id = ee.machine_id
group by m.machine_type, ee.severity
