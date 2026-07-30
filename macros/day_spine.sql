{% macro day_spine(start_expr, end_expr, from_clause) %}
    {{ return(adapter.dispatch('day_spine', 'gea_telemetry')(start_expr, end_expr, from_clause)) }}
{% endmacro %}


{% macro default__day_spine(start_expr, end_expr, from_clause) %}
    select cast(spine_day as date) as day
    from (
        select unnest(generate_series(
            cast({{ start_expr }} as date),
            cast({{ end_expr }} as date),
            interval 1 day
        )) as spine_day
        from {{ from_clause }}
    )
{% endmacro %}


{% macro databricks__day_spine(start_expr, end_expr, from_clause) %}
    select cast(spine_day as date) as day
    from (
        select explode(sequence(
            cast({{ start_expr }} as date),
            cast({{ end_expr }} as date),
            interval 1 day
        )) as spine_day
        from {{ from_clause }}
    )
{% endmacro %}
