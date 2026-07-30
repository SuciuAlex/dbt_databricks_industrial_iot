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
