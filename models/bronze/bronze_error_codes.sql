{{
    config(
        unique_key='error_code',
        incremental_strategy='append'
    )
}}

with source as (

    select * from {{ ref('raw_error_codes') }}

),

cleaned as (

    select
        error_code,
        severity,
        description,
        cast(requires_maintenance as boolean) as requires_maintenance,
        {{ dbt.current_timestamp() }}         as _loaded_at
    from source
    where error_code is not null

)

select * from cleaned

{% if is_incremental() %}
where error_code not in (select error_code from {{ this }})
{% endif %}
