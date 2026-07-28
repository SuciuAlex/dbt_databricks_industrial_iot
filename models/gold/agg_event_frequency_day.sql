{{
    config(
        materialized='view',
        post_hook=[
            "
            merge into {{ ref('silver_tec_watermark') }} as wm
            using (
                select machine_id, event_type_code, max(last_event_timestamp) as new_watermark
                from {{ this }}
                group by machine_id, event_type_code
            ) as src
            on wm.machine_id = src.machine_id and wm.event_type_code = src.event_type_code
            when matched then update set wm.last_processed_event_timestamp = src.new_watermark
            ",
            "{{ log_batch_execution(model_name=this.name) }}"
        ]
    )
}}

-- GOLD LAYER RULE: this model may only ref() silver models (never bronze or
-- raw directly). See CLAUDE.md section 4.4.
--
-- Day-grain event frequency. See agg_event_frequency_minute.sql for the
-- full rationale (independent per-grain scan, watermark/post-hook pattern,
-- and the lag-before-truncate gap semantics) — identical here except for
-- the date_trunc grain.

with watermark as (

    select machine_id, event_type_code, last_processed_event_timestamp
    from {{ ref('silver_tec_watermark') }}

),

new_events as (

    select e.*
    from {{ ref('silver_fact_device_events') }} e
    left join watermark w
        on w.machine_id = e.machine_id
       and w.event_type_code = e.event_type_code
    where e.event_timestamp > coalesce(w.last_processed_event_timestamp, timestamp('1900-01-01'))

),

gapped as (

    select
        machine_id,
        event_type_code,
        event_timestamp,
        event_value,
        unix_timestamp(event_timestamp) - unix_timestamp(
            lag(event_timestamp) over (
                partition by machine_id, event_type_code order by event_timestamp
            )
        ) as seconds_since_prev_event
    from new_events

),

bucketed as (

    select
        machine_id,
        event_type_code,
        date_trunc('day', event_timestamp) as bucket_start,
        event_timestamp,
        event_value,
        seconds_since_prev_event
    from gapped

),

ranked_for_extremes as (

    select
        *,
        row_number() over (
            partition by machine_id, event_type_code, bucket_start
            order by event_value asc, event_timestamp asc
        ) as rn_min,
        row_number() over (
            partition by machine_id, event_type_code, bucket_start
            order by event_value desc, event_timestamp asc
        ) as rn_max
    from bucketed

)

select
    machine_id,
    event_type_code,
    bucket_start,
    count(*)                                           as event_count,
    min(event_timestamp)                                as first_event_timestamp,
    max(event_timestamp)                                as last_event_timestamp,
    max(case when rn_min = 1 then event_timestamp end)  as timestamp_of_min_value,
    max(case when rn_max = 1 then event_timestamp end)  as timestamp_of_max_value,
    avg(seconds_since_prev_event)                       as avg_seconds_between_events
from ranked_for_extremes
group by machine_id, event_type_code, bucket_start
