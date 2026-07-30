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
    {%- set completed_at = modules.datetime.datetime.now(started_at.tzinfo) -%}
    {%- set started_at_literal = started_at.strftime('%Y-%m-%d %H:%M:%S.%f') -%}
    {%- set completed_at_literal = completed_at.strftime('%Y-%m-%d %H:%M:%S.%f') -%}
    {%- set duration_seconds = ((completed_at - started_at).total_seconds()) | round(3) -%}

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
        {{ duration_seconds }}                                                         as duration_seconds,
        cast('{{ started_at_literal }}' as timestamp)                                  as run_started_at,
        cast('{{ completed_at_literal }}' as timestamp)                                as run_completed_at
    from {{ this }}
{% endmacro %}
