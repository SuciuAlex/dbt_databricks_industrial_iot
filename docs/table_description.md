{% docs table_raw_machines %}
Raw seed table with one row per physical machine in the synthetic fleet.
{% enddocs %}

{% docs table_raw_event_types %}
Raw seed table containing the shared event type catalog.
{% enddocs %}

{% docs table_raw_error_codes %}
Raw seed table containing fault/error reference codes and attributes.
{% enddocs %}

{% docs table_raw_device_events %}
Raw seed fact table with one row per emitted machine event across the synthetic time window.
{% enddocs %}

{% docs table_bronze_machines %}
Bronze incremental model with cleaned machine dimension rows from the raw seed.
{% enddocs %}

{% docs table_bronze_event_types %}
Bronze incremental model with cleaned event type dimension rows from the raw seed.
{% enddocs %}

{% docs table_bronze_error_codes %}
Bronze incremental model with cleaned error code dimension rows from the raw seed.
{% enddocs %}

{% docs table_bronze_device_events %}
Bronze incremental fact model with deduplicated and cleaned machine events.
{% enddocs %}

{% docs table_silver_dim_machines %}
Silver SCD2 dimension table tracking machine status history and current state.
{% enddocs %}

{% docs table_silver_fact_device_events %}
Silver conformed event fact table with standardized attributes and event_value.
{% enddocs %}

{% docs table_silver_fact_error_events %}
Silver fact table pairing ERROR_RAISED and ERROR_RESOLVED events to calculate resolution metrics.
{% enddocs %}

{% docs table_silver_tec_watermark %}
Technical silver table storing last processed event timestamp per machine and event type.
{% enddocs %}

{% docs table_silver_tec_kpi_mapping %}
Technical silver table mapping machine and event combinations to KPI codes.
{% enddocs %}

{% docs table_silver_tec_batch_execution_log %}
Technical silver table logging batch execution metrics for watermark-driven models.
{% enddocs %}

{% docs table_dim_machine_status %}
Gold dimension view exposing the current machine status for each machine.
{% enddocs %}

{% docs table_dim_machine_status_history %}
Gold dimension view exposing full machine status history from the silver SCD2 dimension.
{% enddocs %}

{% docs table_agg_machine_uptime_daily %}
Gold aggregate view summarizing daily machine uptime composition.
{% enddocs %}

{% docs table_agg_machine_type_performance %}
Gold aggregate view summarizing daily sensor performance by machine type.
{% enddocs %}

{% docs table_agg_error_analysis %}
Gold aggregate view summarizing error frequency, severity mix, and average resolution metrics.
{% enddocs %}

{% docs table_agg_production_output %}
Gold aggregate view summarizing daily production output and cycle activity.
{% enddocs %}

{% docs table_agg_event_frequency_minute %}
Gold aggregate view of event frequency metrics at minute grain.
{% enddocs %}

{% docs table_agg_event_frequency_hour %}
Gold aggregate view of event frequency metrics at hour grain.
{% enddocs %}

{% docs table_agg_event_frequency_day %}
Gold aggregate view of event frequency metrics at day grain.
{% enddocs %}
