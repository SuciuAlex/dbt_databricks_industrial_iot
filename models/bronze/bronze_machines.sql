{{
    config(
        unique_key='machine_id',
        incremental_strategy='append'
    )
}}

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
    where machine_id is not null

)

select * from cleaned

{% if is_incremental() %}
where machine_id not in (select machine_id from {{ this }})
{% endif %}
