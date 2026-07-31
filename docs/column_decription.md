{% docs column_machine_id %}
Natural key identifying the machine and serving as a common join key across layers.
{% enddocs %}

{% docs column_event_type_code %}
Natural key for the event type, used to join events with the event type catalog.
{% enddocs %}

{% docs column_error_code %}
Natural key for the error/fault code used by fault events.
{% enddocs %}

{% docs column_event_id %}
Primary key of the emitted event record after deduplication logic is applied.
{% enddocs %}

{% docs column_event_timestamp %}
UTC timestamp when the event occurred on the source device.
{% enddocs %}

{% docs column_machine_type %}
Machine process-area classification (SLICER, COOKER, BAKER, PACKER).
{% enddocs %}

{% docs column_model_name %}
Commercial model name of the machine.
{% enddocs %}

{% docs column_manufacturer %}
Manufacturer name for the machine record.
{% enddocs %}

{% docs column_plant_location %}
Plant city or site location where the machine is installed.
{% enddocs %}

{% docs column_plant_country %}
Country where the machine is installed.
{% enddocs %}

{% docs column_install_date %}
Date when the machine was commissioned.
{% enddocs %}

{% docs column_rated_capacity %}
Manufacturer-rated throughput capacity value.
{% enddocs %}

{% docs column_capacity_unit %}
Unit of measure for rated_capacity.
{% enddocs %}

{% docs column_initial_firmware_version %}
Firmware version present at initial commissioning.
{% enddocs %}

{% docs column_event_category %}
High-level category of the event type (lifecycle, production, telemetry, fault, maintenance).
{% enddocs %}

{% docs column_description %}
Human-readable description text for reference entities.
{% enddocs %}

{% docs column_has_numeric_payload %}
Indicates whether the event type normally carries a numeric payload.
{% enddocs %}

{% docs column_severity %}
Severity classification for a fault (LOW, MEDIUM, HIGH, CRITICAL).
{% enddocs %}

{% docs column_requires_maintenance %}
Flag indicating whether the fault typically requires maintenance intervention.
{% enddocs %}

{% docs column_event_date %}
Date component derived from event_timestamp for partition-friendly filtering.
{% enddocs %}

{% docs column_status_value %}
Status value emitted during STATUS_CHANGE events.
{% enddocs %}

{% docs column_temperature_c %}
Temperature reading in degrees Celsius.
{% enddocs %}

{% docs column_speed_units_per_min %}
Machine speed reading in units per minute.
{% enddocs %}

{% docs column_vibration_mm_s %}
Vibration measurement in millimeters per second.
{% enddocs %}

{% docs column_product_count %}
Production counter value used for output-related events.
{% enddocs %}

{% docs column_cycle_duration_seconds %}
Cycle duration in seconds, typically present on CYCLE_COMPLETE events.
{% enddocs %}

{% docs column_source_ingested_at %}
Simulated ingestion timestamp representing warehouse landing time.
{% enddocs %}

{% docs column_machine_sk %}
Surrogate key for a machine SCD2 status version row.
{% enddocs %}

{% docs column_valid_from %}
Timestamp when the SCD2 row became valid.
{% enddocs %}

{% docs column_valid_to %}
Timestamp when the SCD2 row stopped being valid; null means current row.
{% enddocs %}

{% docs column_is_current %}
Boolean flag marking the active SCD2 version for the machine.
{% enddocs %}

{% docs column_event_value %}
Generic numeric payload normalized across event types for aggregated analysis.
{% enddocs %}

{% docs column_resolved_at %}
Timestamp when a raised fault was resolved.
{% enddocs %}

{% docs column_resolution_time_seconds %}
Elapsed seconds between fault raise and resolve timestamps.
{% enddocs %}

{% docs column_load_date %}
Date of the simulated daily gateway load that delivered the row; the batch key bronze appends by and the one a re-delivered event differs on.
{% enddocs %}

{% docs column_loaded_at %}
Audit timestamp stamped by dbt when the row was appended to the bronze landing table.
{% enddocs %}

{% docs column_raised_at %}
Timestamp of the ERROR_RAISED event that opened the fault episode.
{% enddocs %}

{% docs column_error_event_sk %}
Surrogate key of a paired fault episode, derived from machine_id, error_code and raised_at.
{% enddocs %}

{% docs column_firmware_version %}
Firmware version attributed to the machine for this status version.
{% enddocs %}

{% docs column_status_since %}
Timestamp the machine entered its current status (valid_from of the active SCD2 row).
{% enddocs %}

{% docs column_latest_temperature_c %}
Most recent temperature reading in degrees Celsius for the machine.
{% enddocs %}

{% docs column_latest_temperature_at %}
Timestamp of the most recent temperature reading.
{% enddocs %}

{% docs column_latest_speed_units_per_min %}
Most recent speed reading in units per minute for the machine.
{% enddocs %}

{% docs column_latest_speed_at %}
Timestamp of the most recent speed reading.
{% enddocs %}

{% docs column_latest_vibration_mm_s %}
Most recent vibration reading in millimeters per second for the machine.
{% enddocs %}

{% docs column_latest_vibration_at %}
Timestamp of the most recent vibration reading.
{% enddocs %}

{% docs column_total_seconds %}
Total seconds of machine status coverage overlapping the calendar day.
{% enddocs %}

{% docs column_running_seconds %}
Seconds the machine spent in RUNNING status during the calendar day.
{% enddocs %}

{% docs column_down_seconds %}
Seconds the machine spent in STOPPED, MAINTENANCE or ERROR status during the calendar day.
{% enddocs %}

{% docs column_idle_seconds %}
Seconds the machine spent in IDLE status during the calendar day.
{% enddocs %}

{% docs column_pct_running %}
Share of the day's covered seconds spent RUNNING, expressed as a percentage between 0 and 100.
{% enddocs %}

{% docs column_pct_down %}
Share of the day's covered seconds spent STOPPED, MAINTENANCE or ERROR, expressed as a percentage between 0 and 100.
{% enddocs %}

{% docs column_pct_idle %}
Share of the day's covered seconds spent IDLE, expressed as a percentage between 0 and 100.
{% enddocs %}

{% docs column_avg_temperature_c %}
Mean temperature reading in degrees Celsius across the grouped rows.
{% enddocs %}

{% docs column_avg_speed_units_per_min %}
Mean speed reading in units per minute across the grouped rows.
{% enddocs %}

{% docs column_avg_vibration_mm_s %}
Mean vibration reading in millimeters per second across the grouped rows.
{% enddocs %}

{% docs column_temperature_reading_count %}
Number of temperature readings contributing to the group.
{% enddocs %}

{% docs column_speed_reading_count %}
Number of speed readings contributing to the group.
{% enddocs %}

{% docs column_vibration_reading_count %}
Number of vibration readings contributing to the group.
{% enddocs %}

{% docs column_error_count %}
Number of fault episodes in the group.
{% enddocs %}

{% docs column_avg_resolution_time_seconds %}
Mean seconds between fault raise and resolve across the group.
{% enddocs %}

{% docs column_maintenance_required_count %}
Number of fault episodes whose error code requires maintenance intervention.
{% enddocs %}

{% docs column_total_product_count %}
Sum of product counter increments reported by PRODUCT_COUNT_UPDATE events.
{% enddocs %}

{% docs column_cycle_start_count %}
Number of CYCLE_START events in the group.
{% enddocs %}

{% docs column_cycle_complete_count %}
Number of CYCLE_COMPLETE events in the group.
{% enddocs %}

{% docs column_cycle_product_count %}
Sum of product counts reported on CYCLE_COMPLETE events.
{% enddocs %}

{% docs column_avg_cycle_duration_seconds %}
Mean cycle duration in seconds across completed cycles in the group.
{% enddocs %}

{% docs column_bucket_start %}
Start of the time bucket the events were aggregated into (minute, hour or day grain).
{% enddocs %}

{% docs column_event_count %}
Number of events falling in the bucket.
{% enddocs %}

{% docs column_first_event_timestamp %}
Earliest event timestamp within the bucket.
{% enddocs %}

{% docs column_last_event_timestamp %}
Latest event timestamp within the bucket.
{% enddocs %}

{% docs column_timestamp_of_min_value %}
Timestamp of the event holding the lowest event_value in the bucket, ties broken by the earliest timestamp.
{% enddocs %}

{% docs column_timestamp_of_max_value %}
Timestamp of the event holding the highest event_value in the bucket, ties broken by the earliest timestamp.
{% enddocs %}

{% docs column_avg_seconds_between_events %}
True mean of the gaps between consecutive events, measured before bucketing; null only when no preceding event exists.
{% enddocs %}

{% docs column_last_processed_event_timestamp %}
Highest event timestamp already processed for the machine and event type by the watermark-driven models.
{% enddocs %}

{% docs column_kpi_code %}
KPI grouping code for the machine and event type combination; currently the placeholder value all.
{% enddocs %}

{% docs column_batch_run_id %}
Identifier of the dbt invocation that produced the logged batch.
{% enddocs %}

{% docs column_batch_model_name %}
Name of the model whose post-hook wrote the batch log row.
{% enddocs %}

{% docs column_row_count %}
Number of rows the logged batch produced.
{% enddocs %}

{% docs column_distinct_machine_count %}
Number of distinct machines represented in the logged batch.
{% enddocs %}

{% docs column_distinct_event_count %}
Number of distinct event types represented in the logged batch.
{% enddocs %}

{% docs column_duration_seconds %}
Elapsed seconds between the batch start and completion timestamps.
{% enddocs %}

{% docs column_run_started_at %}
Timestamp when the logged batch started.
{% enddocs %}

{% docs column_run_completed_at %}
Timestamp when the logged batch completed.
{% enddocs %}
