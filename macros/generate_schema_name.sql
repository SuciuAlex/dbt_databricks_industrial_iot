{% macro generate_schema_name(custom_schema_name, node) -%}
    {#-
        Force models into the literal schema declared by their folder config
        (raw / bronze / silver / gold) instead of dbt's default
        "<target_schema>_<custom_schema_name>" concatenation. Keeps the four
        medallion schemas clean regardless of which target/environment runs.
    -#}
    {%- if custom_schema_name is none -%}
        {{ target.schema }}
    {%- else -%}
        {{ custom_schema_name | trim }}
    {%- endif -%}
{%- endmacro %}
