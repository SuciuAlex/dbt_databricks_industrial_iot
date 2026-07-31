{{
    config(
        materialized='table'
    )
}}

-- SCD Type 2 dimension, rebuilt as a `table` on every run rather than
-- incremental/merge. Rationale: an incremental SCD2 merge would still need
-- a second statement to patch the previously-current row's valid_to/
-- is_current whenever a new STATUS_CHANGE event lands for a machine — a
-- plain merge-insert alone can't retroactively close out the prior row. At
-- this dataset's scale (a few hundred STATUS_CHANGE events total) a full
-- rebuild is cheap and keeps the window-function logic in one readable
-- query; a higher-volume production version would split this into an
-- incremental "insert new version" step plus a targeted "close out the
-- prior current row" update.
--
-- SILVER OWNS DATA QUALITY (CLAUDE.md section 4.3): bronze appends every
-- batch as-is, so both the machine dimension and the STATUS_CHANGE events
-- are deduplicated here before the SCD2 windows are built. Without this a
-- re-delivered STATUS_CHANGE would produce two versions sharing one
-- valid_from and break the machine_sk uniqueness invariant.

with machines as (

    select *
    from {{ ref('bronze_machines') }}
    qualify row_number() over (partition by machine_id order by _loaded_at desc) = 1

),

status_events as (

    select
        event_id,
        machine_id,
        event_timestamp,
        status_value
    from {{ ref('bronze_device_events') }}
    where event_type_code = 'STATUS_CHANGE'
      and machine_id is not null
    qualify row_number() over (
        partition by event_id order by source_ingested_at desc, _loaded_at desc
    ) = 1

),

status_changes as (

    -- One status version per machine + instant, so valid_from (and therefore
    -- machine_sk) stays unique even if two events share a timestamp.
    select
        machine_id,
        event_timestamp,
        status_value
    from status_events
    qualify row_number() over (
        partition by machine_id, event_timestamp order by event_id
    ) = 1

),

versioned as (

    select
        m.machine_id,
        m.machine_type,
        m.plant_location,
        m.initial_firmware_version                                             as firmware_version,
        sc.status_value,
        sc.event_timestamp                                                     as valid_from,
        lead(sc.event_timestamp) over (
            partition by m.machine_id order by sc.event_timestamp
        )                                                                       as valid_to
    from status_changes sc
    inner join machines m on m.machine_id = sc.machine_id

)

select
    {{ dbt_utils.generate_surrogate_key(['machine_id', 'valid_from']) }} as machine_sk,
    machine_id,
    machine_type,
    status_value,
    plant_location,
    firmware_version,
    valid_from,
    valid_to,
    valid_to is null as is_current
from versioned
