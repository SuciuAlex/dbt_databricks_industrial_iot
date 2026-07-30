# CLAUDE.md — GEA Industrial Telemetry: dbt-on-Databricks Showcase

## 0. Purpose of this document

This file is the build specification for a demo repository that showcases the core
architectural benefits of **dbt** running on **Databricks**. It is meant to be handed
to Claude Code, which will scaffold the project, generate the synthetic data, write the
models, and validate the build end-to-end.

The repo must demonstrate, concretely and runnably:

1. A clean **raw → bronze → silver → gold** medallion architecture.
2. **`ref()`-only** model wiring so the full DAG is inferable and `dbt docs generate`
   produces a complete lineage graph — no hardcoded table names anywhere.
3. **dbt tests** (`not_null`, `unique`, `relationships`, `accepted_values`) at every layer.
4. **Incremental-only** materialization in bronze.
5. **SCD Type 2** history tracking in silver.
6. **View-only** gold models that select exclusively from silver.
7. The power of **`dbt build --select +model_name+`** to rebuild an exact upstream +
   downstream slice of the DAG.

The business domain is synthetic IoT telemetry from **GEA**-style industrial machines
(cooking, baking, slicing, packaging equipment).

---

## 1. Tech stack & project shape

| Component        | Choice |
|-------------------|--------|
| Warehouse          | Databricks (Unity Catalog) |
| Transformation     | dbt-core + `dbt-databricks` adapter |
| Catalog            | `gea_demo` (single catalog, four schemas) |
| Schemas            | `raw`, `bronze`, `silver`, `gold` |
| Project name       | `gea_telemetry` |
| Seed data generator | Python (`pandas` + `numpy`, fixed random seed for reproducibility) |

Claude Code should scaffold a standard dbt project:

```
gea_telemetry/
├── CLAUDE.md
├── dbt_project.yml
├── packages.yml                 # dbt_utils, dbt_expectations (optional but recommended)
├── profiles.yml.example
├── .claude/
│   └── skills/
│       ├── data-architect-jira-refiner/SKILL.md
│       ├── jira-worker/SKILL.md
│       ├── data-engineer/SKILL.md
│       ├── code-reviewer/SKILL.md
│       └── tester/SKILL.md
├── seeds/
│   ├── raw_machines.csv
│   ├── raw_event_types.csv
│   ├── raw_error_codes.csv
│   ├── raw_device_events.csv
│   └── seeds_properties.yml
├── models/
│   ├── raw/
│   │   └── raw_sources.yml      # doc + tests for the seed-backed "raw" layer
│   ├── bronze/
│   │   ├── bronze_machines.sql
│   │   ├── bronze_event_types.sql
│   │   ├── bronze_error_codes.sql
│   │   ├── bronze_device_events.sql
│   │   └── bronze.yml
│   ├── silver/
│   │   ├── silver_dim_machines.sql          # SCD2
│   │   ├── silver_fact_device_events.sql
│   │   ├── silver_fact_error_events.sql
│   │   ├── silver_tec_watermark.sql         # batch watermark control table
│   │   ├── silver_tec_kpi_mapping.sql       # machine+event -> KPI mapping
│   │   ├── silver_tec_batch_execution_log.sql # batch run telemetry log
│   │   └── silver.yml
│   └── gold/
│       ├── dim_machine_status.sql           # active row only
│       ├── dim_machine_status_history.sql   # full SCD2 history, exposed
│       ├── agg_machine_uptime_daily.sql
│       ├── agg_machine_type_performance.sql
│       ├── agg_error_analysis.sql
│       ├── agg_production_output.sql
│       ├── agg_event_frequency_minute.sql
│       ├── agg_event_frequency_hour.sql
│       ├── agg_event_frequency_day.sql
│       └── gold.yml
├── tests/                       # singular dbt tests
│   └── assert_no_overlapping_scd2_periods.sql
├── tests/soda/                  # SODA data-quality checks (see section 10)
│   ├── configuration.yml
│   ├── checks/
│   │   ├── checks_silver_fact_device_events.yml
│   │   ├── checks_agg_event_frequency.yml
│   │   └── checks_silver_dim_machines.yml
│   └── scripts/
│       └── run_soda_scan.py
├── macros/
│   ├── generate_schema_name.sql
│   └── log_batch_execution.sql  # post-hook macro, see section 4.5
└── scripts/
    └── generate_synthetic_data.py
```

`generate_schema_name.sql` should force models to land in the schema declared by their
folder config (`raw` / `bronze` / `silver` / `gold`) rather than
`<target_schema>_bronze`, so the four schemas are clean and literal.

### 1.1 Naming convention (applies across the whole project)

| Layer | Prefix rule | Type codes | Example |
|---|---|---|---|
| bronze | always `bronze_<name>` | **none** — bronze objects never carry a `dim_`/`fact_`/`tec_` code | `bronze_machines`, `bronze_device_events` |
| silver | always `silver_<code>_<name>` | `dim_`, `fact_`, `tec_` (see below) | `silver_dim_machines`, `silver_fact_device_events`, `silver_tec_watermark` |
| gold | **no** `gold_` prefix, but keeps the type code | `dim_`, `fact_`, `agg_`, `rel_`, `tec_` | `dim_machine_status`, `agg_event_frequency_hour` |

Type codes, used from silver onward:

| Code | Meaning |
|---|---|
| `dim_` | Dimension / attribute table |
| `fact_` | Fact / event-grain table |
| `agg_` | Pre-aggregated table |
| `rel_` | Bridge/relationship table between two other entities |
| `tec_` | Technical table: telemetry, logs, watermarks, mappings — not meant for business consumption |

**Gold-specific rule:** gold objects that source from an SCD2 (or otherwise
change-tracked) silver table expose **only the currently-active row** by default
(e.g. `dim_machine_status`). Where the historical trail is also useful to expose,
add a second gold object with the same name plus an **`_history`** suffix (e.g.
`dim_machine_status_history`). The `_history` suffix is used **only** for `dim_`
gold objects — `agg_`/`fact_` gold objects are already time-bucketed/historical by
construction and do not get a `_history` twin.

---

## 2. Domain model: GEA machine fleet

### 2.1 Machine types (4)

| machine_type | GEA process area      |
|--------------|------------------------|
| `SLICER`     | Slicing                |
| `COOKER`     | Cooking                |
| `BAKER`      | Baking                 |
| `PACKER`     | Packaging              |

### 2.2 Machine IDs (5 per type → 20 machines total)

Pattern: `<TYPE_PREFIX>-<3-digit sequence>`

- `SLC-001` … `SLC-005`
- `CKR-001` … `CKR-005`
- `BKR-001` … `BKR-005`
- `PKR-001` … `PKR-005`

### 2.3 Event types (10, shared catalog across machine types)

A single, generic event catalog keeps the fact table's schema uniform across machine
types (payload columns are simply `NULL` where not applicable) — this mirrors how real
IoT gateways emit a common event envelope.

| event_type_code              | category   | description | drives |
|-------------------------------|------------|-------------|--------|
| `STATUS_CHANGE`               | lifecycle  | Machine transitions between `RUNNING`, `IDLE`, `STOPPED`, `MAINTENANCE`, `ERROR` | **silver SCD2** |
| `CYCLE_START`                 | production | A production/process cycle begins | gold production output |
| `CYCLE_COMPLETE`               | production | A production/process cycle ends, with cycle duration | gold production output |
| `SENSOR_TEMPERATURE_READING`  | telemetry  | Core temperature reading (°C) — relevant to `COOKER`/`BAKER` | gold performance |
| `SENSOR_SPEED_READING`        | telemetry  | Line/blade speed (units/min) — relevant to `SLICER`/`PACKER` | gold performance |
| `SENSOR_VIBRATION_READING`    | telemetry  | Vibration amplitude (mm/s) — relevant to all, esp. `SLICER` | gold performance |
| `PRODUCT_COUNT_UPDATE`        | production | Running output counter increment | gold production output |
| `ERROR_RAISED`                | fault      | Fault raised, references `error_code` | gold error analysis, silver SCD2 |
| `ERROR_RESOLVED`              | fault      | Fault cleared, references `error_code` | gold error analysis |
| `MAINTENANCE_ALERT`           | maintenance| Preventive/predictive maintenance flag | gold uptime/maintenance |

### 2.4 Error codes (~15–20 rows)

Small reference seed: `error_code`, `severity` (`LOW`/`MEDIUM`/`HIGH`/`CRITICAL`),
`description`, `requires_maintenance` (bool). Examples: `E-101 Blade misalignment`,
`E-204 Oven temperature deviation`, `E-310 Conveyor jam`, `E-450 Packaging seal failure`,
`E-500 Emergency stop triggered`.

---

## 3. Synthetic data specification (all loaded as **dbt seeds**)

All synthetic data ships as CSVs in `seeds/`, generated by
`scripts/generate_synthetic_data.py` with a **fixed random seed** so the dataset is
reproducible. **Hard cap: total rows across all seed files must stay under 1,000,000.**

| Seed file              | Grain                          | Approx. rows | Notes |
|-------------------------|--------------------------------|-------------:|-------|
| `raw_machines.csv`      | 1 row per machine               | 20 | dimension |
| `raw_event_types.csv`   | 1 row per event type             | 10 | dimension |
| `raw_error_codes.csv`   | 1 row per error code             | ~18 | dimension |
| `raw_device_events.csv` | 1 row per emitted event          | **~800,000** | fact — see below |
| **Total**                |                                  | **~800,048** | comfortably under the 1M cap |

### 3.1 `raw_machines.csv`

Columns: `machine_id`, `machine_type`, `model_name`, `manufacturer` (`"GEA Group"`),
`plant_location`, `plant_country`, `install_date`, `rated_capacity`, `capacity_unit`,
`initial_firmware_version`.

### 3.2 `raw_event_types.csv`

Columns: `event_type_code`, `event_category`, `description`, `has_numeric_payload` (bool).

### 3.3 `raw_error_codes.csv`

Columns: `error_code`, `severity`, `description`, `requires_maintenance`.

### 3.4 `raw_device_events.csv` — the fact seed

Columns:

| column | type | notes |
|---|---|---|
| `event_id` | string (UUID) | primary key, `unique` + `not_null` tests |
| `machine_id` | string | FK to machines |
| `machine_type` | string | denormalized for convenience, matches machine |
| `event_type_code` | string | FK to event types |
| `event_timestamp` | timestamp | ISO 8601, 3-month span |
| `event_date` | date | partition-friendly derived column |
| `status_value` | string, nullable | populated only for `STATUS_CHANGE` (`RUNNING`/`IDLE`/`STOPPED`/`MAINTENANCE`/`ERROR`) |
| `temperature_c` | float, nullable | populated for `SENSOR_TEMPERATURE_READING` (and `COOKER`/`BAKER` bias) |
| `speed_units_per_min` | float, nullable | populated for `SENSOR_SPEED_READING` (`SLICER`/`PACKER` bias) |
| `vibration_mm_s` | float, nullable | populated for `SENSOR_VIBRATION_READING` |
| `product_count` | int, nullable | populated for `PRODUCT_COUNT_UPDATE` and `CYCLE_COMPLETE` |
| `cycle_duration_seconds` | int, nullable | populated for `CYCLE_COMPLETE` |
| `error_code` | string, nullable | populated for `ERROR_RAISED` / `ERROR_RESOLVED` |
| `source_ingested_at` | timestamp | simulated ingestion timestamp, `event_timestamp + small random lag` |

### 3.5 Generation rules

- **Time span:** exactly 3 months (e.g. `2026-04-01` through `2026-06-30`).
- **Volume target:** average ~450 events/machine/day across 20 machines × 90 days ≈
  **810,000 rows**; tune per-event frequencies below until total lands in the
  700k–850k range.
- **Diurnal/weekly pattern:** higher event density during simulated "shift hours"
  (06:00–22:00) and on weekdays; reduced overnight/weekend traffic — makes gold uptime
  aggregations meaningful.
- **Per-event relative frequency (guideline weights, tune to hit volume target):**
  - `SENSOR_TEMPERATURE_READING`, `SENSOR_SPEED_READING`, `SENSOR_VIBRATION_READING`: high frequency, every ~10–15 min during operation.
  - `PRODUCT_COUNT_UPDATE`: every ~5–10 min during operation.
  - `CYCLE_START` / `CYCLE_COMPLETE`: paired, several dozen per machine per day.
  - `STATUS_CHANGE`: low frequency — target **15–30 transitions per machine over the
    full 3 months**, cycling through `RUNNING → IDLE → RUNNING → MAINTENANCE → RUNNING → ERROR → RUNNING → STOPPED …`. This is what feeds the silver SCD2 model, so it must be sparse but present for every machine.
  - `ERROR_RAISED` / `ERROR_RESOLVED`: rare, occasional bursts (simulate a handful of fault episodes per machine over 3 months), always paired (a resolve follows a raise), referencing `raw_error_codes`.
  - `MAINTENANCE_ALERT`: rare, correlate loosely with upcoming `STATUS_CHANGE → MAINTENANCE` events.
- **Machine-type sensor bias:** `COOKER`/`BAKER` skew temperature readings higher
  (120–220 °C range) with slow drift; `SLICER`/`PACKER` skew speed + vibration
  readings; all types occasionally emit all sensor types (realistic multi-sensor
  gateways), just with different means/variance.
- **Data quality noise (intentional, for the tests to catch / bronze to clean):**
  inject a small number (<0.05%) of duplicate `event_id`s and a few rows with null
  `machine_id` into the raw seed, then have bronze models deduplicate/filter them —
  this makes the `not_null`/`unique` tests at the bronze layer meaningfully pass
  *because* of the transformation, not by accident.

---

## 4. Layer-by-layer model design

### 4.1 Raw layer — seeds

The four CSVs above **are** the raw layer. Configure in `dbt_project.yml`:

```yaml
seeds:
  gea_telemetry:
    +schema: raw
    +quote_columns: false
    raw_device_events:
      +column_types:
        event_timestamp: timestamp
        source_ingested_at: timestamp
```

Document and test the seeds directly in `seeds/seeds_properties.yml` (seeds are
`ref()`-able, so downstream bronze models reference them like any other model — this
satisfies the "everything wired with `ref()`" requirement even at the very first hop).

### 4.2 Bronze layer — **incremental only**

Every bronze model uses `materialized: incremental`. Folder-level default in
`dbt_project.yml`:

```yaml
models:
  gea_telemetry:
    bronze:
      +materialized: incremental
      +schema: bronze
      +tags: ['bronze']
      +on_schema_change: fail
```

Models:

- **`bronze_machines`** — `ref('raw_machines')`, light typing/cleanup, `unique_key='machine_id'`, `incremental_strategy='append'`.
- **`bronze_event_types`** — `ref('raw_event_types')`, `unique_key='event_type_code'`, `incremental_strategy='append'`.
- **`bronze_error_codes`** — `ref('raw_error_codes')`, `unique_key='error_code'`, `incremental_strategy='append'`.
- **`bronze_device_events`** — `ref('raw_device_events')`, the flagship incremental
  model:
  - `unique_key='event_id'`, `incremental_strategy='append'`.
  - Deduplicate on `event_id` (`qualify row_number() over (partition by event_id order by source_ingested_at desc) = 1`).
  - Drop/quarantine rows with null `machine_id` (route to a `bronze_device_events_rejects` model or simply filter with a documented rationale).
  - `is_incremental()` filter: `where event_timestamp > (select max(event_timestamp) from {{ this }})`.
  - Cast/standardize types, add `_loaded_at` audit column.

**Demo payoff:** running `dbt build` a second time with no new seed rows shows bronze
incremental models processing **zero new rows** when the model's incremental filter
is set correctly (no-op), directly illustrating why incremental materialization
avoids full-table rescans — a natural talking point in the repo's README. Note: the
project uses an `append` incremental strategy in the bronze layer; deduplication and
delta filters (e.g. `where event_timestamp > (select max(event_timestamp) from {{ this }})`)
ensure we do not insert duplicate historical rows on re-runs.

### 4.3 Silver layer — **SCD Type 2 + technical control tables**

Folder default:

```yaml
models:
  gea_telemetry:
    silver:
      +schema: silver
      +tags: ['silver']
```

**Business models:**

- **`silver_dim_machines`** (materialized `incremental` + `incremental_strategy='merge'`,
  or `table` if simplicity is preferred for the demo — document the tradeoff in the
  model's doc block either way):
  - Sources: `ref('bronze_machines')` (attribute baseline) joined with
    `STATUS_CHANGE` rows from `ref('bronze_device_events')`.
  - Build history with window functions:
    ```sql
    valid_from = event_timestamp
    valid_to   = lead(event_timestamp) over (partition by machine_id order by event_timestamp)
    is_current = valid_to is null
    ```
  - Surrogate key: `{{ dbt_utils.generate_surrogate_key(['machine_id','valid_from']) }}`.
  - Columns: `machine_sk`, `machine_id`, `machine_type`, `status_value`, `plant_location`,
    `firmware_version`, `valid_from`, `valid_to`, `is_current`.
  - This is the canonical SCD2 table other models join to for "status as of time T" or
    "current status" lookups.

- **`silver_fact_device_events`** (materialized `table`):
  - `ref('bronze_device_events')` joined to `ref('bronze_machines')` and
    `ref('bronze_event_types')`, conformed column names, one row per event — the
    cleaned, business-ready event fact.
  - Adds a generic **`event_value`** column (float, nullable), populated per
    `event_type_code` from whichever type-specific payload column applies —
    `temperature_c` for `SENSOR_TEMPERATURE_READING`, `speed_units_per_min` for
    `SENSOR_SPEED_READING`, `vibration_mm_s` for `SENSOR_VIBRATION_READING`,
    `product_count` for `PRODUCT_COUNT_UPDATE` / `CYCLE_COMPLETE`. `NULL` for event
    types with no natural numeric payload (`STATUS_CHANGE`, `ERROR_RAISED`,
    `ERROR_RESOLVED`, `MAINTENANCE_ALERT`, `CYCLE_START`). This single column is what
    lets the gold event-frequency models (section 4.6) define "highest/lowest value
    in the bucket" unambiguously regardless of event type.

- **`silver_fact_error_events`** (materialized `table`):
  - Derived from `ref('silver_fact_device_events')`, pairs `ERROR_RAISED` →
    `ERROR_RESOLVED` per `machine_id` + `error_code` (window/self-join pattern) to
    compute `resolution_time_seconds`, joined to `ref('bronze_error_codes')` for
    severity.

**Technical (`tec_`) control models** — not business-facing, support the batch
processing pattern used by the gold event-frequency feature (full detail in
section 4.5):

- **`silver_tec_watermark`** — one row per `machine_id` + `event_type_code`, holding
  `last_processed_event_timestamp`. Pipeline-maintained state: each consuming model
  updates its own watermark rows via `merge` after it finishes processing a batch.
- **`silver_tec_kpi_mapping`** — maps every `machine_id` + `event_type_code`
  combination to a `kpi_code`. Materialized `incremental`, built as a cross-join of
  distinct `machine_id` (from `ref('bronze_machines')`) and distinct
  `event_type_code` (from `ref('bronze_event_types')`), defaulting `kpi_code = 'all'`
  for every combination (no specific KPIs defined yet — `all` is a placeholder
  ensuring every machine/event row is picked up by any KPI-level aggregation added
  later). **Important:** this model must run an *incremental* scan — on each run it
  should only insert `machine_id`/`event_type_code` combinations that are **not
  already present** in the target (anti-join / `where not exists` against
  `{{ this }}`), not re-derive and re-load the full cross-join every time. This way
  new machines or event types that show up in later batches are picked up
  automatically without disturbing existing mappings.
- **`silver_tec_batch_execution_log`** — one row per batch run of a watermark-driven
  model, written via the post-hook macro described in section 4.5. Columns:
  `batch_run_id`, `model_name`, `row_count`, `distinct_machine_count`,
  `distinct_event_count`, `duration_seconds`, `run_started_at`, `run_completed_at`.

### 4.4 Gold layer — **views only, silver-only sources**

Folder default:

```yaml
models:
  gea_telemetry:
    gold:
      +materialized: view
      +schema: gold
      +tags: ['gold']
```

**Hard rule (enforce in code review / model doc headers): gold models may only
`ref()` silver models — never bronze or raw directly.** Add a short comment block at
the top of every gold `.sql` file stating this, and spot-check with:
`grep -L "ref('silver_" models/gold/*.sql` (should return nothing).

**Active-row vs. history convention:** any gold `dim_` object derived from an SCD2
silver table exposes only `is_current = true` by default. Where history is useful,
a second `_history` object exposes the full trail. Only `dim_` objects get this
treatment (section 1.1).

Models:

- **`dim_machine_status`** — `is_current = true` slice of `ref('silver_dim_machines')`, joined with the latest sensor reading per machine from `ref('silver_fact_device_events')`.
- **`dim_machine_status_history`** — full historical trail from `ref('silver_dim_machines')` (all `valid_from`/`valid_to` rows, not filtered to current), for anyone needing "what was the status at time T" or a status timeline.
- **`agg_machine_uptime_daily`** — daily `%RUNNING` vs `%STOPPED/MAINTENANCE/ERROR` per machine, derived from `silver_dim_machines` interval overlap against calendar days.
- **`agg_machine_type_performance`** — average temperature/speed/vibration by `machine_type` and day, from `silver_fact_device_events`.
- **`agg_error_analysis`** — error frequency, mean resolution time, severity mix by `machine_type`, from `silver_fact_error_events`.
- **`agg_production_output`** — daily product counts and cycle counts/durations per machine, from `silver_fact_device_events`.
- **`agg_event_frequency_minute`**, **`agg_event_frequency_hour`**, **`agg_event_frequency_day`** — see section 4.6.

This fan-in/fan-out (multiple gold views depending on the same one or two silver
models) is intentional: it's what makes `--select +model+` demonstrations compelling.

### 4.5 Batch control pattern: watermark, KPI mapping, and execution log

This pattern exists specifically to support the event-frequency feature (section
4.6) with a realistic, production-style incremental batch design, while staying
simple enough for a demo.

**Flow:**

1. An `agg_event_frequency_*` model starts a run, generates a `batch_run_id`
   (e.g. `{{ invocation_id }}` or a generated UUID captured at the start of the
   model), and reads `ref('silver_tec_watermark')` to determine, per
   `machine_id` + `event_type_code`, the `last_processed_event_timestamp` from the
   previous run.
2. It selects only rows from `ref('silver_fact_device_events')` with
   `event_timestamp > last_processed_event_timestamp` (falling back to
   `'1900-01-01'` for combinations with no watermark row yet — first run).
3. It computes the bucketed aggregation (see 4.6) over that incremental slice and
   inserts/merges the results.
4. It **updates `silver_tec_watermark`** (via a `merge` in a `post-hook`, or an
   explicit statement at the end of the model) setting
   `last_processed_event_timestamp = max(event_timestamp)` processed in this run,
   per `machine_id` + `event_type_code`.
5. A **post-hook macro**, `log_batch_execution()` (in `macros/log_batch_execution.sql`),
   fires after the model completes and inserts one row into
   `silver_tec_batch_execution_log` with the run's `batch_run_id`, `{{ this.name }}`
   as `model_name`, the row count produced, `count(distinct machine_id)`,
   `count(distinct event_type_code)`, and the elapsed duration (captured via a
   `run_started_at` variable set at the top of the model and compared to
   `current_timestamp()` in the hook).

**Scope for this demo:** the watermark table, the post-hook logging macro, and the
KPI mapping table are used by the **three `agg_event_frequency_*` models only** —
they are not wired up as a project-wide default. This keeps the pattern legible
as a focused showcase rather than a blanket framework applied to every model.

Example post-hook wiring on one of the frequency models:

```sql
{{
  config(
    materialized = 'view',
    post_hook = "{{ log_batch_execution(model_name=this.name) }}"
  )
}}
```

### 4.6 Gold event-frequency views (`agg_event_frequency_minute` / `_hour` / `_day`)

Three independent gold objects, one per time grain, **each scanning
`ref('silver_fact_device_events')` directly** (not built on top of one another —
this was a deliberate choice: rolling hour up from minute would make the
"average time between events" metric an approximation rather than a true mean of
consecutive-event gaps, so each grain is computed independently from the raw event
grain to keep that metric exact).

**Grain:** one row per `machine_id` + `event_type_code` + time bucket
(`bucket_start`, truncated to minute/hour/day respectively).

**Columns (identical shape across all three models, differing only in truncation
grain):**

| column | definition |
|---|---|
| `machine_id` | bucket key |
| `event_type_code` | bucket key |
| `bucket_start` | `date_trunc('minute'/'hour'/'day', event_timestamp)` |
| `event_count` | `count(*)` of events in the bucket |
| `first_event_timestamp` | `min(event_timestamp)` in the bucket |
| `last_event_timestamp` | `max(event_timestamp)` in the bucket |
| `timestamp_of_min_value` | `event_timestamp` of the row where `event_value` is at its minimum in the bucket (ties broken by earliest timestamp) |
| `timestamp_of_max_value` | `event_timestamp` of the row where `event_value` is at its maximum in the bucket (ties broken by earliest timestamp) |
| `avg_seconds_between_events` | the **true mean** of `event_timestamp - lag(event_timestamp)` gaps between consecutive events within the bucket, partitioned by `machine_id` + `event_type_code` and ordered by `event_timestamp` (i.e. genuinely "every 0.73 seconds", not a span/count approximation) — `NULL` when a bucket has only 1 event (no gap to measure) |

**Implementation approach:** compute per-event gaps with a `lag()` window function
over `silver_fact_device_events` (partitioned by `machine_id`, `event_type_code`,
ordered by `event_timestamp`) *before* truncating to the bucket, then aggregate
(`count`, `min`, `max`, `avg`) grouped by the truncated bucket — this way the gap
calculation naturally respects true event-to-event spacing while still reporting
per-bucket.

**Watermark + logging:** all three models follow the pattern in section 4.5 —
incremental read via `silver_tec_watermark`, watermark update at the end of the
run, and a `log_batch_execution()` post-hook writing to
`silver_tec_batch_execution_log`.

---

## 5. Testing strategy

Apply generic tests via YAML in every layer's `.yml` file; add a couple of singular
tests for anything a generic test can't express.

| Layer | Model | Tests |
|---|---|---|
| raw (seeds) | `raw_machines` | `unique`+`not_null` on `machine_id` |
| raw (seeds) | `raw_event_types` | `unique`+`not_null` on `event_type_code`; `accepted_values` on `event_category` |
| raw (seeds) | `raw_error_codes` | `unique`+`not_null` on `error_code`; `accepted_values` on `severity` |
| bronze | `bronze_machines` | `unique`+`not_null` on `machine_id`; `accepted_values` on `machine_type` |
| bronze | `bronze_device_events` | `unique`+`not_null` on `event_id`; `not_null` on `machine_id`, `event_timestamp`; `relationships` to `bronze_machines.machine_id` and `bronze_event_types.event_type_code` |
| silver | `silver_dim_machines` | `not_null` on `machine_sk`, `valid_from`; `unique` on `machine_sk`; singular test asserting no overlapping `[valid_from, valid_to)` ranges per `machine_id`; `dbt_utils.accepted_range`-style check that exactly one `is_current = true` row exists per `machine_id` |
| silver | `silver_fact_device_events` | `unique`+`not_null` on `event_id`; `relationships` to `silver_dim_machines.machine_id` |
| silver | `silver_fact_error_events` | `not_null` on `machine_id`, `error_code`, `raised_at`; `relationships` to `bronze_error_codes.error_code` |
| silver | `silver_tec_watermark` | `unique` on combination of `machine_id`+`event_type_code` (via `dbt_utils.unique_combination_of_columns`); `not_null` on `last_processed_event_timestamp` |
| silver | `silver_tec_kpi_mapping` | `unique` on combination of `machine_id`+`event_type_code`+`kpi_code`; `not_null` on `kpi_code`; `accepted_values` including `'all'` |
| silver | `silver_tec_batch_execution_log` | `not_null`+`unique` on `batch_run_id`+`model_name`; `not_null` on `run_started_at`, `run_completed_at` |
| gold | all | `not_null` on grain keys (`machine_id`, `event_date`, etc.); `dbt_expectations.expect_column_values_to_be_between` (or a simple `expression_is_true`) on percentage columns being 0–100 |
| gold | `agg_event_frequency_minute`/`_hour`/`_day` | `not_null` on `machine_id`, `event_type_code`, `bucket_start`, `event_count`; `unique` on combination of `machine_id`+`event_type_code`+`bucket_start`; `dbt_expectations.expect_column_values_to_be_between` on `event_count` being `>= 1` |

Add `packages.yml` with `dbt-labs/dbt_utils` (surrogate keys, `accepted_range`) and,
optionally, `calogica/dbt_expectations` for the percentage-range checks.

Singular test example (`tests/assert_no_overlapping_scd2_periods.sql`): self-join
`silver_machines_scd2` on `machine_id` where one row's `valid_from` falls strictly
inside another row's `[valid_from, valid_to)` window; test fails if any rows return.

---

## 6. Lineage & selector showcase

Because **every** model uses `ref()` (seeds included) and nothing references a
hardcoded table name, `dbt docs generate && dbt docs serve` renders a complete DAG:
`raw seeds → bronze (4) → silver (3) → gold (5)`.

Document these commands in the repo README as the "money shot" demos:

```bash
# Full build, all layers, respecting the DAG
dbt build

# Rebuild everything upstream AND downstream of one silver model —
# shows dbt resolving the whole dependency chain from a single node
dbt build --select +silver_fact_device_events+

# Rebuild just the bronze layer and everything it feeds
dbt build --select bronze.* --select bronze.*+

# Rebuild only what changed since the last run (state-based, if using dbt Cloud/CI)
dbt build --select state:modified+

# Layer-only builds via tags
dbt build --select tag:gold
```

Recommend `bronze_device_events` and `silver_dim_machines` as the two "hero nodes"
for `--select +model+` walkthroughs, since one shows deep upstream-only fan-in
(seeds) and the other shows rich downstream fan-out (`dim_machine_status`,
`dim_machine_status_history`, and `agg_machine_uptime_daily` all depend on it).

---

## 7. Naming & config conventions

- Model file name = model name = table name (no schema prefixing in the file name).
- Every model gets a `.yml` doc entry with a `description`, at least a PK test, and
  column-level descriptions for any non-obvious field.
- Use `{{ config(...) }}` blocks or folder-level `dbt_project.yml` defaults
  consistently — don't mix both for the same setting.
- All timestamps stored as `timestamp` (UTC), no local-time ambiguity.
- Every SQL model must resolve all table references through `ref()` or `source()`
  (there are no `source()`s in this project since raw = seeds; seeds are always
  referenced through `ref()`).

---

## 8. SODA data-quality testing (`tests/soda/`)

In addition to dbt's built-in generic/singular tests, the repo includes a
**separate, parallel data-quality layer using SODA (SODA Core / SODA CL)**,
living entirely under `tests/soda/` at the repo root — independent from the dbt
`tests/` folder used for singular dbt tests.

```
tests/soda/
├── configuration.yml        # SODA data source config, pointed at Databricks/Spark
├── checks/
│   ├── checks_silver_fact_device_events.yml
│   ├── checks_agg_event_frequency.yml
│   └── checks_silver_dim_machines.yml
└── scripts/
    └── run_soda_scan.py     # invokes SODA scans against the configured checks
```

**`configuration.yml`** should configure a SODA `spark` (Databricks) data source
using the same connection details as the dbt Databricks profile (workspace host,
HTTP path, catalog, and a token sourced from an environment variable — never
hardcoded). Claude Code should scaffold this file with placeholders and a comment
pointing at where to source credentials from (env vars matching the dbt
`profiles.yml` conventions).

**Checks to include, at minimum:**

- `checks_silver_dim_machines.yml` — row count > 0; no duplicate `machine_sk`;
  freshness check on `valid_from`; a SODA check replicating the "no overlapping
  SCD2 periods" invariant (can be expressed as a SQL-based custom SODA check).
- `checks_silver_fact_device_events.yml` — row count > 0; `event_id` uniqueness;
  `event_value` is non-null wherever `event_type_code` is a sensor/count event
  type; no future-dated `event_timestamp`.
- `checks_agg_event_frequency.yml` — `event_count >= 1` for all rows;
  `avg_seconds_between_events` is null only when `event_count = 1`;
  `bucket_start` values fall within the synthetic dataset's 3-month window.

**`run_soda_scan.py`** should be a small, well-documented Python script that loads
`configuration.yml`, runs all check files under `checks/`, and exits non-zero on
any failed check (suitable for CI). It is deliberately kept separate from the dbt
run so SODA checks can be run independently (e.g. `python tests/soda/scripts/run_soda_scan.py`)
without requiring a full `dbt build`.

---

## 9. Agent skills (`.claude/skills/`)

The repo defines five role-specific skills under `.claude/skills/`, each its own
`SKILL.md`. These are personas/playbooks for Claude Code (or other Claude agents)
to adopt when working different parts of the delivery lifecycle for this project.
Each skill is designed to be used **independently** — a given skill should not
assume or defer to the judgment of another skill's agent; each must reach its own
conclusions from first principles.

| Skill folder | Role |
|---|---|
| `data-architect-jira-refiner` | Turns vague asks into well-formed Jira tickets: clear acceptance criteria, dbt layer/model impact, links to existing models, complexity/sizing flags. |
| `jira-worker` | Polls/reads assigned Jira tickets, works the described dbt task, posts status updates, transitions ticket state. |
| `data-engineer` | Implements dbt models/macros/tests per this CLAUDE.md's architecture and naming conventions. |
| `code-reviewer` | Expert dbt/Databricks reviewer; reviews implementation PRs strictly on technical merit, independent of what the architect/dev agents concluded. |
| `tester` | Expert dbt/Databricks tester; assumes upstream agents may have gotten things wrong, hunts for edge cases, and authors SODA checks in `tests/soda/`. |

**Important constraints Claude Code must honor when writing these skill files**
(all agreed with the requester — see below for the exact spec of each):

- The **Jira-related skills** (`data-architect-jira-refiner`, `jira-worker`) must
  be written **generically**, describing workflow and responsibilities without
  assuming any specific Jira MCP connector or tool function names — no live Jira
  connector was verified for this project. Each must open with an explicit
  instruction to discover whatever Jira-capable tool is actually available in the
  session at runtime (MCP connector, or otherwise) and use its real interface,
  rather than assuming a fixed API.
- The **`code-reviewer`** skill must explicitly instruct the agent to reach its
  own independent technical conclusions and avoid being anchored or influenced by
  the architect, dev, or any other agent's prior output — it reviews the code as
  it stands against dbt/Databricks best practice and this CLAUDE.md, not against
  what previous agents claimed.
- The **`tester`** skill must explicitly instruct the agent to assume the
  architect, dev, and reviewer agents may have made mistakes, and to actively
  hunt for edge cases (empty buckets, single-event buckets, watermark-table
  first-run behavior, duplicate `event_id`s, null `machine_id`s, SCD2 boundary
  overlaps, timezone edge cases, etc.) rather than simply confirming the happy
  path. It must also be capable of writing complex SODA checks in Python
  (`tests/soda/`), and must **never hallucinate** — every claim about actual
  behavior must be verified by running dbt/SQL/SODA and reading the real output,
  not assumed.

Each `SKILL.md` should follow standard skill-file structure (name, description,
trigger conditions, step-by-step responsibilities, and any tool-use guidance),
consistent with the other skills already present in this environment.

---

## 10. Implementation checklist for Claude Code

1. Scaffold the dbt project structure in section 1, including `.claude/skills/`
   and `tests/soda/`.
2. Write `scripts/generate_synthetic_data.py` implementing section 3; run it to
   produce the four CSVs in `seeds/`; print final row counts and assert the
   <1,000,000 total-row cap.
3. `dbt seed` to load raw data.
4. Implement bronze models (section 4.2) — incremental, merge strategy, dedup logic.
5. Implement silver business models (section 4.3) — SCD2 window-function logic for
   `silver_dim_machines`; conformed fact tables `silver_fact_device_events` (incl.
   the `event_value` column) and `silver_fact_error_events`.
6. Implement silver technical models (section 4.3) — `silver_tec_watermark`,
   `silver_tec_kpi_mapping` (incremental anti-join scan), `silver_tec_batch_execution_log`.
7. Implement `macros/log_batch_execution.sql` (section 4.5) — the post-hook macro
   that writes to `silver_tec_batch_execution_log`.
8. Implement gold models (section 4.4/4.6) — views only, silver-only refs;
   `dim_machine_status` (+ `_history`), the four `agg_` business views, and the
   three `agg_event_frequency_*` views wired to the watermark + post-hook pattern.
9. Write all YAML docs + tests (section 5); add `packages.yml` and run `dbt deps`.
10. Add the singular dbt test(s), including the no-overlapping-SCD2-periods check.
11. `dbt build` end-to-end; confirm 0 failures.
12. `dbt build` a second time with no seed changes; confirm bronze incremental
    models process 0 new rows, and confirm the `agg_event_frequency_*` models'
    watermark-driven read also processes 0 new rows on the second run (screenshot/
    log this for the README).
13. Scaffold `tests/soda/` (section 8) — `configuration.yml`, the three check
    files, and `run_soda_scan.py`; run it against the built tables and confirm
    all checks pass.
14. Write the five `SKILL.md` files under `.claude/skills/` (section 9).
15. `dbt docs generate`; confirm the DAG renders raw→bronze→silver→gold cleanly,
    including the `tec_` control tables and their consumers.
16. Write a top-level `README.md` summarizing the showcase and the exact commands
    from section 6, including the incremental-no-op proof from step 12 and how to
    run the SODA scan from step 13.
