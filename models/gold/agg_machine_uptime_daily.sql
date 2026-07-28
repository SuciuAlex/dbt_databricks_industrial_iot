{{ config(materialized='view') }}

-- GOLD LAYER RULE: this model may only ref() silver models (never bronze or
-- raw directly). See CLAUDE.md section 4.4.
--
-- Daily %RUNNING vs %STOPPED/MAINTENANCE/ERROR per machine, computed by
-- overlapping each silver_dim_machines SCD2 interval against a calendar-day
-- spine (native Spark/Databricks sequence()+explode(), rather than
-- dbt_utils.date_spine, to keep the day-generation SQL Databricks-native).

with scd2 as (

    select
        machine_id,
        machine_type,
        status_value,
        valid_from,
        coalesce(valid_to, current_timestamp()) as valid_to
    from {{ ref('silver_dim_machines') }}

),

day_spine as (

    select explode(sequence(
        (select min(cast(valid_from as date)) from scd2),
        (select max(cast(valid_to as date)) from scd2),
        interval 1 day
    )) as day

),

machines as (

    select distinct machine_id, machine_type from scd2

),

machine_days as (

    select
        m.machine_id,
        m.machine_type,
        ds.day
    from machines m
    cross join day_spine ds

),

overlap as (

    select
        md.machine_id,
        md.machine_type,
        md.day,
        s.status_value,
        greatest(
            0,
            unix_timestamp(least(s.valid_to, timestamp(md.day) + interval 1 day))
            - unix_timestamp(greatest(s.valid_from, timestamp(md.day)))
        ) as overlap_seconds
    from machine_days md
    inner join scd2 s
        on s.machine_id = md.machine_id
       and s.valid_from < timestamp(md.day) + interval 1 day
       and s.valid_to   > timestamp(md.day)

),

daily_totals as (

    select
        machine_id,
        machine_type,
        day,
        sum(overlap_seconds) as total_seconds,
        sum(case when status_value = 'RUNNING' then overlap_seconds else 0 end)                    as running_seconds,
        sum(case when status_value in ('STOPPED', 'MAINTENANCE', 'ERROR') then overlap_seconds else 0 end) as down_seconds,
        sum(case when status_value = 'IDLE' then overlap_seconds else 0 end)                        as idle_seconds
    from overlap
    group by machine_id, machine_type, day

)

select
    machine_id,
    machine_type,
    day as event_date,
    total_seconds,
    running_seconds,
    down_seconds,
    idle_seconds,
    round(100.0 * running_seconds / nullif(total_seconds, 0), 2) as pct_running,
    round(100.0 * down_seconds / nullif(total_seconds, 0), 2)    as pct_down,
    round(100.0 * idle_seconds / nullif(total_seconds, 0), 2)    as pct_idle
from daily_totals
