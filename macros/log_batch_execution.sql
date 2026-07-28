{% macro log_batch_execution(model_name, model_started_at=none) %}
    {#-
        Post-hook: writes one row to silver_tec_batch_execution_log describing
        this batch run. Used only by the watermark-driven agg_event_frequency_*
        gold models (section 4.5/4.6 of CLAUDE.md) — not a project-wide hook.

        model_started_at: an optional Python datetime captured near the top of
        the calling model (e.g. {% set model_started_at =
        modules.datetime.datetime.utcnow() %}) for a per-model duration. Falls
        back to dbt's built-in `run_started_at` (invocation start) if omitted.
    -#}
    {%- set started_at = model_started_at or run_started_at -%}
    {%- set started_at_literal = started_at.strftime('%Y-%m-%d %H:%M:%S.%f') -%}

    insert into {{ ref('silver_tec_batch_execution_log') }}
    (
        batch_run_id,
        model_name,
        row_count,
        distinct_machine_count,
        distinct_event_count,
        duration_seconds,
        run_started_at,
        run_completed_at
    )
    select
        '{{ invocation_id }}'                                                          as batch_run_id,
        '{{ model_name }}'                                                             as model_name,
        count(*)                                                                       as row_count,
        count(distinct machine_id)                                                     as distinct_machine_count,
        count(distinct event_type_code)                                                as distinct_event_count,
        unix_timestamp(current_timestamp()) - unix_timestamp(timestamp('{{ started_at_literal }}')) as duration_seconds,
        timestamp('{{ started_at_literal }}')                                          as run_started_at,
        current_timestamp()                                                            as run_completed_at
    from {{ this }}
{% endmacro %}
