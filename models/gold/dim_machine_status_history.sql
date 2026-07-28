{{ config(materialized='view') }}

-- GOLD LAYER RULE: this model may only ref() silver models (never bronze or
-- raw directly). See CLAUDE.md section 4.4.
--
-- Full historical trail (every valid_from/valid_to version, not filtered to
-- is_current) for anyone needing "what was the status at time T" or a
-- status timeline. See dim_machine_status for the active-row-only view.

select
    machine_sk,
    machine_id,
    machine_type,
    status_value,
    plant_location,
    firmware_version,
    valid_from,
    valid_to,
    is_current
from {{ ref('silver_dim_machines') }}
