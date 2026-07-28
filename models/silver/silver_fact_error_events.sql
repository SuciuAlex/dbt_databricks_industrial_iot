{{
    config(
        materialized='table'
    )
}}

-- Pairs ERROR_RAISED -> ERROR_RESOLVED per machine_id + error_code using a
-- lead() window over the error events, computing resolution_time_seconds.
-- Assumes fault episodes for a given machine_id + error_code do not
-- overlap (true by construction in the synthetic generator), so the next
-- ERROR_RESOLVED chronologically after an ERROR_RAISED is its match.

with error_events as (

    select
        machine_id,
        error_code,
        event_type_code,
        event_timestamp
    from {{ ref('silver_fact_device_events') }}
    where event_type_code in ('ERROR_RAISED', 'ERROR_RESOLVED')

),

paired as (

    select
        machine_id,
        error_code,
        event_type_code,
        event_timestamp,
        lead(event_timestamp) over (
            partition by machine_id, error_code order by event_timestamp
        ) as next_event_timestamp,
        lead(event_type_code) over (
            partition by machine_id, error_code order by event_timestamp
        ) as next_event_type_code
    from error_events

),

raised_resolved as (

    select
        machine_id,
        error_code,
        event_timestamp      as raised_at,
        next_event_timestamp as resolved_at
    from paired
    where event_type_code = 'ERROR_RAISED'
      and next_event_type_code = 'ERROR_RESOLVED'

)

select
    {{ dbt_utils.generate_surrogate_key(['rr.machine_id', 'rr.error_code', 'rr.raised_at']) }} as error_event_sk,
    rr.machine_id,
    rr.error_code,
    ec.severity,
    ec.requires_maintenance,
    rr.raised_at,
    rr.resolved_at,
    unix_timestamp(rr.resolved_at) - unix_timestamp(rr.raised_at) as resolution_time_seconds
from raised_resolved rr
inner join {{ ref('bronze_error_codes') }} ec on ec.error_code = rr.error_code
