{{
    config(
        materialized='incremental',
        unique_key=['machine_id', 'event_type_code'],
        incremental_strategy='merge'
    )
}}

-- Technical control table: maps every machine_id + event_type_code
-- combination to a kpi_code, defaulting to 'all' (no specific KPIs are
-- defined yet — 'all' is a placeholder ensuring every combination is
-- picked up by any future KPI-level aggregation). Runs as an anti-join
-- incremental scan so new machines/event types picked up in later seed
-- loads are added automatically without disturbing existing mappings
-- (which a human or downstream process may have since customized).

with combos as (

    select distinct
        m.machine_id,
        et.event_type_code
    from {{ ref('bronze_machines') }} m
    cross join {{ ref('bronze_event_types') }} et

)

select
    c.machine_id,
    c.event_type_code,
    'all' as kpi_code
from combos c

{% if is_incremental() %}
where not exists (
    select 1
    from {{ this }} t
    where t.machine_id = c.machine_id
      and t.event_type_code = c.event_type_code
)
{% endif %}
