{{
    config(
        materialized='incremental',
        unique_key=['batch_run_id', 'model_name'],
        incremental_strategy='merge',
        on_schema_change='fail'
    )
}}

-- Technical control table: one row per batch run of a watermark-driven
-- model, written by the log_batch_execution() post-hook macro (see
-- macros/log_batch_execution.sql) called from the three
-- agg_event_frequency_* gold models. This model has no natural source
-- query of its own — every real row arrives via that post-hook INSERT.
-- Materialized `incremental` (not `table`) purely so this model's own
-- build step never truncates history that earlier runs' post-hooks already
-- wrote; the SELECT below intentionally always returns zero rows, its only
-- purpose is to establish/carry the table's schema for ref()/merge to work
-- against.

select
    cast(null as string)    as batch_run_id,
    cast(null as string)    as model_name,
    cast(null as bigint)    as row_count,
    cast(null as bigint)    as distinct_machine_count,
    cast(null as bigint)    as distinct_event_count,
    cast(null as bigint)    as duration_seconds,
    cast(null as timestamp) as run_started_at,
    cast(null as timestamp) as run_completed_at
where false
