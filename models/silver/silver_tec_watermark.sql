{{
    config(
        materialized='incremental',
        unique_key=['machine_id', 'event_type_code'],
        incremental_strategy='merge'
    )
}}

-- Technical control table: one row per machine_id + event_type_code,
-- holding the watermark consumed by the agg_event_frequency_* gold models
-- (section 4.5/4.6). Pipeline-maintained state — those models advance
-- last_processed_event_timestamp themselves via a post-hook merge once
-- they finish processing a batch. This model's own job is only to make
-- sure every machine/event-type combination has a starting row; it must
-- never overwrite a combination that already exists (that would clobber
-- progress another model already made), so it anti-joins against {{ this }}
-- and only ever inserts genuinely new combinations.

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
    timestamp('1900-01-01 00:00:00') as last_processed_event_timestamp
from combos c

{% if is_incremental() %}
where not exists (
    select 1
    from {{ this }} t
    where t.machine_id = c.machine_id
      and t.event_type_code = c.event_type_code
)
{% endif %}
