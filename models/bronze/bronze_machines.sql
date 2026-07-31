{{
    config(
        incremental_strategy='append'
    )
}}

-- BRONZE LAYER RULE (CLAUDE.md section 4.2): append-only landing zone. Every
-- run re-appends the reference seed, so this table may hold several versions
-- of the same machine_id. silver_dim_machines picks the latest per machine.

with source as (

    select * from {{ ref('raw_machines') }}

),

cleaned as (

    select
        machine_id,
        machine_type,
        model_name,
        manufacturer,
        plant_location,
        plant_country,
        cast(install_date as date)     as install_date,
        cast(rated_capacity as double) as rated_capacity,
        capacity_unit,
        initial_firmware_version,
        {{ dbt.current_timestamp() }}  as _loaded_at
    from source

)

select * from cleaned
