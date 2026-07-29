{% docs column_agg_error_analysis %}
Error frequency, mean resolution time, and severity mix by machine_type, from silver_fact_error_events.
{% enddocs %}

{% docs column_agg_event_frequency_day %}
Day-grain event frequency, one row per machine_id + event_type_code + bucket_start. Watermark-driven incremental read via silver_tec_watermark; post-hooks advance the watermark and log the batch to silver_tec_batch_execution_log (section 4.5/4.6).
{% enddocs %}

{% docs column_agg_event_frequency_hour %}
Hour-grain event frequency, one row per machine_id + event_type_code + bucket_start. Watermark-driven incremental read via silver_tec_watermark; post-hooks advance the watermark and log the batch to silver_tec_batch_execution_log (section 4.5/4.6).
{% enddocs %}

{% docs column_agg_event_frequency_minute %}
Minute-grain event frequency, one row per machine_id + event_type_code + bucket_start. Watermark-driven incremental read via silver_tec_watermark; post-hooks advance the watermark and log the batch to silver_tec_batch_execution_log (section 4.5/4.6).
{% enddocs %}

{% docs column_agg_machine_type_performance %}
Average temperature/speed/vibration by machine_type and day, from silver_fact_device_events.
{% enddocs %}

{% docs column_agg_machine_uptime_daily %}
Daily %RUNNING vs %STOPPED/MAINTENANCE/ERROR per machine, computed by overlapping silver_dim_machines SCD2 intervals against a calendar-day spine.
{% enddocs %}

{% docs column_agg_production_output %}
Daily product counts and cycle counts/durations per machine, from silver_fact_device_events.
{% enddocs %}

{% docs column_avg_cycle_duration_seconds %}
Average duration of completed cycles in seconds.
{% enddocs %}

{% docs column_avg_resolution_time_seconds %}
Average resolution time in seconds.
{% enddocs %}

{% docs column_avg_seconds_between_events %}
Average time between consecutive events in the bucket.
{% enddocs %}

{% docs column_avg_speed_units_per_min %}
Average speed reading for the day.
{% enddocs %}

{% docs column_avg_temperature_c %}
Average temperature reading for the day.
{% enddocs %}

{% docs column_avg_vibration_mm_s %}
Average vibration reading for the day.
{% enddocs %}

{% docs column_batch_run_id %}
Unique batch execution identifier.
{% enddocs %}

{% docs column_bronze_device_events %}
Incremental (merge) cleanup of `raw_device_events`: deduplicates on `event_id` (keeping the latest-ingested copy) and drops rows with a null `machine_id`. On subsequent runs, only reads rows newer than the max `event_timestamp` already loaded (`is_incremental()` filter) — running `dbt build` a second time with unchanged seed data processes zero new rows here.
{% enddocs %}

{% docs column_bronze_error_codes %}
Incremental (merge) cleanup of `raw_error_codes`. One row per fault code in the reference catalog.
{% enddocs %}

{% docs column_bronze_event_types %}
Incremental (merge) cleanup of `raw_event_types`. One row per event type in the shared event catalog.
{% enddocs %}

{% docs column_bronze_machines %}
Incremental (merge) cleanup of `raw_machines`: light typing, drops any row with a null `machine_id`. One row per machine.
{% enddocs %}

{% docs column_bucket_start %}
Truncated bucket start timestamp for the bucket grain.
{% enddocs %}

{% docs column_capacity_unit %}
Unit for `rated_capacity`, varies by `machine_type`.
{% enddocs %}

{% docs column_cycle_complete_count %}
Count of cycle complete events.
{% enddocs %}

{% docs column_cycle_duration_seconds %}
Populated only for `CYCLE_COMPLETE` events.
{% enddocs %}

{% docs column_cycle_product_count %}
Total product count attributed to completed cycles.
{% enddocs %}

{% docs column_cycle_start_count %}
Count of cycle start events.
{% enddocs %}

{% docs column_description %}
Human-readable description of what the event represents.
{% enddocs %}

{% docs column_dim_machine_status %}
Active-row (is_current = true) slice of silver_dim_machines, joined with each machine's latest sensor reading. See dim_machine_status_history for the full trail.
{% enddocs %}

{% docs column_dim_machine_status_history %}
Full historical SCD2 trail from silver_dim_machines (all valid_from/valid_to versions), for "status as of time T" lookups.
{% enddocs %}

{% docs column_distinct_event_count %}
Distinct event types processed in the batch.
{% enddocs %}

{% docs column_distinct_machine_count %}
Distinct machines processed in the batch.
{% enddocs %}

{% docs column_down_seconds %}
Seconds in STOPPED/MAINTENANCE/ERROR.
{% enddocs %}

{% docs column_duration_seconds %}
Execution duration of the batch in seconds.
{% enddocs %}

{% docs column_error_code %}
Natural key, FK target for downstream models.
{% enddocs %}

{% docs column_error_count %}
Count of errors.
{% enddocs %}

{% docs column_event_category %}
High-level grouping of the event type.
{% enddocs %}

{% docs column_event_count %}
Number of events in the bucket.
{% enddocs %}

{% docs column_event_date %}
Date part of `event_timestamp`, provided for partition-friendly filtering.
{% enddocs %}

{% docs column_event_id %}
Deduplicated primary key of the event.
{% enddocs %}

{% docs column_event_timestamp %}
UTC timestamp the event occurred.
{% enddocs %}

{% docs column_event_type_code %}
Natural key, FK target for downstream models.
{% enddocs %}

{% docs column_event_value %}
Type-specific numeric payload normalized into one column (temperature for sensor-temperature events, speed for sensor-speed events, etc.); null for event types with no natural numeric payload.
{% enddocs %}

{% docs column_first_event_timestamp %}
Timestamp of the first event in the bucket.
{% enddocs %}

{% docs column_has_numeric_payload %}
Whether this event type carries a meaningful numeric payload value.
{% enddocs %}

{% docs column_idle_seconds %}
Seconds IDLE in the day.
{% enddocs %}

{% docs column_initial_firmware_version %}
Firmware version installed at commissioning time.
{% enddocs %}

{% docs column_install_date %}
Date the machine was commissioned at its plant.
{% enddocs %}

{% docs column_is_current %}
True when `valid_to` is null (the currently-active row for this machine).
{% enddocs %}

{% docs column_kpi_code %}
KPI mapping code currently defaulted to all.
{% enddocs %}

{% docs column_last_event_timestamp %}
Timestamp of the last event in the bucket.
{% enddocs %}

{% docs column_latest_speed_at %}
Timestamp of the latest speed reading.
{% enddocs %}

{% docs column_latest_speed_units_per_min %}
Latest speed reading value for the machine.
{% enddocs %}

{% docs column_latest_temperature_at %}
Timestamp of the latest temperature reading.
{% enddocs %}

{% docs column_latest_temperature_c %}
Latest temperature reading value for the machine.
{% enddocs %}

{% docs column_latest_vibration_at %}
Timestamp of the latest vibration reading.
{% enddocs %}

{% docs column_latest_vibration_mm_s %}
Latest vibration reading value for the machine.
{% enddocs %}

{% docs column_machine_id %}
Natural key, FK target for downstream models.
{% enddocs %}

{% docs column_machine_sk %}
Surrogate key, `generate_surrogate_key(['machine_id', 'valid_from'])`.
{% enddocs %}

{% docs column_machine_type %}
One of the four GEA process areas.
{% enddocs %}

{% docs column_maintenance_required_count %}
Count of errors requiring maintenance.
{% enddocs %}

{% docs column_manufacturer %}
Always "GEA Group" for this fleet.
{% enddocs %}

{% docs column_model_name %}
Commercial model name of the machine.
{% enddocs %}

{% docs column_pct_down %}
Percent of daily time in DOWN/ERROR/MAINTENANCE.
{% enddocs %}

{% docs column_pct_idle %}
Percent of daily time in IDLE.
{% enddocs %}

{% docs column_pct_running %}
Percent of daily time in RUNNING.
{% enddocs %}

{% docs column_plant_country %}
Country where the machine is installed.
{% enddocs %}

{% docs column_plant_location %}
City where the machine is installed.
{% enddocs %}

{% docs column_product_count %}
Populated for `PRODUCT_COUNT_UPDATE` and `CYCLE_COMPLETE` events.
{% enddocs %}

{% docs column_rated_capacity %}
Manufacturer-rated throughput capacity, in `capacity_unit`.
{% enddocs %}

{% docs column_raw_device_events %}
Raw fact seed: one row per event emitted by a machine's IoT gateway over a 3-month synthetic window (~800k rows). This seed intentionally contains a small amount of data-quality noise — a handful of duplicate `event_id`s and a few rows with a null `machine_id` — which `bronze_device_events` is responsible for cleaning up. No generic tests are applied at this layer for that reason; the bronze layer's `unique`/`not_null` tests are what demonstrate the cleanup actually working.
{% enddocs %}

{% docs column_raw_error_codes %}
Raw dimension seed: fault/error reference catalog referenced by `ERROR_RAISED` / `ERROR_RESOLVED` device events.
{% enddocs %}

{% docs column_raw_event_types %}
Raw dimension seed: the shared event-type catalog emitted by every machine's IoT gateway, regardless of machine type (payload columns are simply NULL where not applicable to a given event).
{% enddocs %}

{% docs column_raw_machines %}
Raw dimension seed: one row per physical GEA machine in the fleet (20 machines across 4 process areas). This is the raw layer for the demo — loaded via `dbt seed` and referenced downstream exclusively through `ref('raw_machines')`.
{% enddocs %}

{% docs column_requires_maintenance %}
Whether this fault typically requires a maintenance intervention to clear.
{% enddocs %}

{% docs column_resolution_time_seconds %}
Seconds between raised_at and resolved_at.
{% enddocs %}

{% docs column_resolved_at %}
Timestamp the paired ERROR_RESOLVED event occurred.
{% enddocs %}

{% docs column_row_count %}
Number of rows produced by the batch.
{% enddocs %}

{% docs column_run_completed_at %}
Timestamp when the batch run completed.
{% enddocs %}

{% docs column_run_started_at %}
Timestamp when the batch run started.
{% enddocs %}

{% docs column_running_seconds %}
Seconds RUNNING in the day.
{% enddocs %}

{% docs column_severity %}
Severity classification of the fault.
{% enddocs %}

{% docs column_silver_dim_machines %}
SCD Type 2 dimension: one row per machine per status-attribute version. Built from `bronze_machines` joined with `STATUS_CHANGE` events from `bronze_device_events`; `valid_from`/`valid_to` derived with a `lead()` window per `machine_id`. This is the canonical table other models join to for "status as of time T" or "current status" lookups.
{% enddocs %}

{% docs column_silver_fact_device_events %}
Conformed, business-ready event fact — one row per device event, with machine/event-type attributes joined in and a generic `event_value` column populated from whichever type-specific payload column applies.
{% enddocs %}

{% docs column_silver_fact_error_events %}
Derived from `silver_fact_device_events`: pairs `ERROR_RAISED` -> `ERROR_RESOLVED` per `machine_id` + `error_code`, computing `resolution_time_seconds`, joined to `bronze_error_codes` for severity.
{% enddocs %}

{% docs column_silver_tec_batch_execution_log %}
Technical control table (not business-facing): one row per batch run of a watermark-driven model, written entirely via the log_batch_execution() post-hook macro — this model's own defining query always returns zero rows.
{% enddocs %}

{% docs column_silver_tec_kpi_mapping %}
Technical control table (not business-facing): maps every machine_id + event_type_code combination to a kpi_code, defaulting to 'all' as a placeholder until specific KPIs are defined.
{% enddocs %}

{% docs column_silver_tec_watermark %}
Technical control table (not business-facing): one row per machine_id + event_type_code holding last_processed_event_timestamp, consumed and advanced by the agg_event_frequency_* gold models.
{% enddocs %}

{% docs column_source_ingested_at %}
Simulated ingestion timestamp (`event_timestamp` plus a small random lag).
{% enddocs %}

{% docs column_speed_units_per_min %}
Populated only for `SENSOR_SPEED_READING` events.
{% enddocs %}

{% docs column_status_since %}
Timestamp when this current status became active.
{% enddocs %}

{% docs column_status_value %}
Populated only for `STATUS_CHANGE` events.
{% enddocs %}

{% docs column_temperature_c %}
Populated only for `SENSOR_TEMPERATURE_READING` events.
{% enddocs %}

{% docs column_timestamp_of_max_value %}
Event timestamp of the maximum payload value in the bucket.
{% enddocs %}

{% docs column_timestamp_of_min_value %}
Event timestamp of the minimum payload value in the bucket.
{% enddocs %}

{% docs column_total_product_count %}
Total product count for the day.
{% enddocs %}

{% docs column_total_seconds %}
Total seconds of status overlap in the day.
{% enddocs %}

{% docs column_valid_from %}
Timestamp this version of the machine's status became effective.
{% enddocs %}

{% docs column_valid_to %}
Timestamp this version stopped being effective; null for the current version.
{% enddocs %}

{% docs column_vibration_mm_s %}
Populated only for `SENSOR_VIBRATION_READING` events.
{% enddocs %}
