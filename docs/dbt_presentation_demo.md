% Dbt Demo: Showcase Guide

Purpose
-------
This demo file provides a concise, runnable set of dbt commands and talking points you can use during a presentation to demonstrate dbt's strengths: reproducible transformations, clear lineage (DAG), testing and data quality, incremental materializations, modularity, and docs.

Quick Setup (one-time)
----------------------
- Ensure your virtual environment and dbt deps are installed:

```bash
python -m venv .venv
source .venv/bin/activate   # (or .venv\\Scripts\\activate on Windows)
pip install -r requirements.txt  # if you have one; otherwise install dbt
dbt deps
```

Presentation Flow
-----------------
1. Project orientation (files, layers): point to the raw → bronze → silver → gold folders and explain the medallion pattern.
2. Show seeds and `dbt seed` to demonstrate deterministic inputs.
3. Run incremental bronze to show fast re-runs.
4. Run `dbt build` demonstrations (including `++` selection).
5. Show dbt tests and data-quality checks.
6. Generate and open dbt docs to show the DAG and centralized docs.
7. Explain advanced selection (tags, state:, --models syntax) and CI-friendly commands.
8. Walk the **targeted raw → gold scenario** (see below) end-to-end for a single machine, following the same rows through every layer in Databricks SQL.

Commands & Talking Points
-------------------------

1) Show reproducible inputs

```bash
# Load seed data (raw layer is in seeds/)
dbt seed --select raw_*
```

Talking point: Seeds let you ship small, deterministic datasets with the repo so demos are reproducible and reviewers can run locally.

2) Run the bronze incremental models

```bash
dbt build --select tag:bronze
```

Talking point: Bronze models are incremental (merge strategy). Re-running with unchanged seeds produces zero processed rows — fast no-ops.

3) Build a focused slice with upstream + downstream (`++`)

```bash
# Rebuild a model plus everything upstream and downstream (useful for demos)
dbt build --select +silver_fact_device_events+

# Equivalent: rebuild only one model and its entire lineage
dbt build --select ++silver_dim_machines++
```

Talking point: `+` selects parents, `++` selects parents and children recursively. Use `--select` to scope builds for speed and demos.

4) Run tests and show failures

```bash
# Run all generic tests declared in schema yml files
dbt test

# Run tests just for one layer or model
dbt test --select tag:gold
```

Talking point: Tests live with models; they are SQL-based and run as part of CI. Failing tests provide actionable rows for debugging.

5) Show docs and DAG

```bash
# Generate docs artifacts
dbt docs generate

# Serve docs locally (interactive DAG/column docs)
dbt docs serve
```

Talking point: dbt docs serve exposes an interactive DAG (lineage), searchable column docs, and model descriptions. Use centralized doc blocks so multiple schema files reference the same descriptions.

6) Demonstrate model selection, tags, and state-based runs

```bash
# Re-run modified models only (in CI after a change)
dbt build --select state:modified+

# Run models by tag
dbt build --select tag:gold
```

Talking point: Selection syntax is powerful (`+`, `@`, `tag:`, `path:`). `state:` enables incremental CI workflows that re-run only changed models.

7) Show logs, artifacts, and compiled SQL

```bash
# View compiled SQL for a model
dbt compile --select silver_fact_device_events
less target/compiled/<your_project>/models/silver/silver_fact_device_events.sql

# Run the model SQL directly (sanity checks)
dbt run --select silver_fact_device_events
```

Talking point: `dbt compile` and the `target/` directory expose the compiled SQL you can audit or copy to other systems.

8) Show documentation best-practice: centralized doc blocks

Talking point: Keep column descriptions in one docs file and reference with `description: "{{ doc('column_x') }}"` in your schema YMLs. This prevents duplication and ensures consistent docs across models.

9) CI / reproducibility snippet (example)

```bash
# Example CI job (pseudo-steps)
pip install -r requirements.txt
dbt deps
dbt seed --profiles-dir .profiles
dbt build --profiles-dir .profiles --select tag:bronze++
dbt test --profiles-dir .profiles
dbt docs generate --profiles-dir .profiles
```

Targeted Scenario: One Machine, Raw → Gold
------------------------------------------

This is the "follow the data" demo. We take a **single machine and event type**,
push a small new batch into raw, and watch the exact same rows travel through
bronze (dedup + quarantine), silver (conformed fact + SCD2), and finally land in
`agg_event_frequency_minute` in gold. Every step has a dbt command *and* a
Databricks SQL query so the audience sees the physical effect, not just log output.

**Demo constants** (swap freely — they are only used to keep the queries short):

| Placeholder | Value used below |
|---|---|
| Catalog | `gea_demo` |
| Machine | `SLC-001` (a slicer) |
| Event type | `SENSOR_VIBRATION_READING` |
| New-batch date | `2026-07-01` (one day *after* the synthetic 3-month window ends) |

### Step 0 — Establish the "before" picture

```sql
-- 0.1 Where does the existing data stop? This is the high-water mark that
--     bronze's incremental filter will compare against on the next run.
select
    count(*)                as raw_rows,
    min(event_timestamp)    as first_event,
    max(event_timestamp)    as last_event
from gea_demo.raw.raw_device_events
where machine_id = 'SLC-001'
  and event_type_code = 'SENSOR_VIBRATION_READING';
```

```sql
-- 0.2 Same question against bronze. Bronze should already be slightly SMALLER
--     than raw overall, because duplicates and null-machine rows were dropped.
select
    count(*)             as bronze_rows,
    max(event_timestamp) as bronze_watermark,
    max(_loaded_at)      as last_dbt_load
from gea_demo.bronze.bronze_device_events
where machine_id = 'SLC-001'
  and event_type_code = 'SENSOR_VIBRATION_READING';
```

Talking point: raw is what the gateway sent us, warts and all. Bronze is the first
place where we take responsibility for the data.

### Step 1 — Simulate a new load into raw

The seed CSV is deterministic, so for a live demo we append a tiny batch directly to
the raw table. The batch is deliberately *dirty*: 4 clean events, 1 re-delivered
duplicate, and 1 malformed row with no `machine_id`.

```sql
-- 1.1 DEMO-ONLY WRITE: append a 6-row "new gateway batch" to raw.
--     Note the timestamps are all in the same minute (10:00) — that minute is the
--     bucket we will inspect in gold at the end.
--     Row 4 and row 5 share the SAME event_id (a re-delivery, ingested later).
--     Row 6 has a NULL machine_id (a malformed payload).
insert into gea_demo.raw.raw_device_events
    (event_id, machine_id, machine_type, event_type_code, event_timestamp, event_date,
     status_value, temperature_c, speed_units_per_min, vibration_mm_s,
     product_count, cycle_duration_seconds, error_code, source_ingested_at)
values
    ('demo-0001', 'SLC-001', 'SLICER', 'SENSOR_VIBRATION_READING', timestamp'2026-07-01 10:00:05', date'2026-07-01', null, null, null, 2.10, null, null, null, timestamp'2026-07-01 10:00:20'),
    ('demo-0002', 'SLC-001', 'SLICER', 'SENSOR_VIBRATION_READING', timestamp'2026-07-01 10:00:20', date'2026-07-01', null, null, null, 4.80, null, null, null, timestamp'2026-07-01 10:00:35'),
    ('demo-0003', 'SLC-001', 'SLICER', 'SENSOR_VIBRATION_READING', timestamp'2026-07-01 10:00:35', date'2026-07-01', null, null, null, 1.20, null, null, null, timestamp'2026-07-01 10:00:50'),
    ('demo-0004', 'SLC-001', 'SLICER', 'SENSOR_VIBRATION_READING', timestamp'2026-07-01 10:00:50', date'2026-07-01', null, null, null, 3.30, null, null, null, timestamp'2026-07-01 10:01:05'),
    ('demo-0004', 'SLC-001', 'SLICER', 'SENSOR_VIBRATION_READING', timestamp'2026-07-01 10:00:50', date'2026-07-01', null, null, null, 3.30, null, null, null, timestamp'2026-07-01 10:06:05'),
    ('demo-0005', null,      'SLICER', 'SENSOR_VIBRATION_READING', timestamp'2026-07-01 10:00:55', date'2026-07-01', null, null, null, 9.90, null, null, null, timestamp'2026-07-01 10:01:10');
```

```sql
-- 1.2 Prove the batch landed in raw exactly as sent: 6 rows, 5 distinct event_ids,
--     1 row missing its machine_id. Raw keeps the mess on purpose.
select
    count(*)                                                as rows_landed,
    count(distinct event_id)                                 as distinct_event_ids,
    sum(case when machine_id is null then 1 else 0 end)      as null_machine_rows
from gea_demo.raw.raw_device_events
where event_date = date'2026-07-01';
```

```sql
-- 1.3 The duplicate, side by side. Same event_id, same reading — only
--     source_ingested_at differs (the second delivery arrived 5 minutes later).
select event_id, machine_id, event_timestamp, vibration_mm_s, source_ingested_at
from gea_demo.raw.raw_device_events
where event_id = 'demo-0004'
order by source_ingested_at;
```

> If you prefer a fully repeatable, no-manual-SQL variant: add the same six rows to
> `seeds/raw_device_events.csv` and run `dbt seed --select raw_device_events --full-refresh`.

### Step 2 — Build the exact slice that leads to gold

```bash
# 2.1 Build EVERYTHING upstream of the target gold model, in dependency order:
#     seeds -> bronze (4) -> silver (fact, dim, tec) -> agg_event_frequency_minute.
#     '+model' = the model plus all its ancestors. Tests run inline because it's `build`.
dbt build --select +agg_event_frequency_minute
```

```bash
# 2.2 Same slice, but ALSO everything downstream (nothing here, by design —
#     good moment to show that gold is a leaf and the DAG knows it).
dbt build --select +agg_event_frequency_minute+
```

```bash
# 2.3 Narrow it further: just the bronze hop, to isolate the incremental behaviour.
dbt build --select bronze_device_events
```

Talking point: one selector expressed the whole raw→gold path. Nobody had to know
the execution order — `ref()` did.

### Step 3 — Bronze: what cleanup actually happened

```sql
-- 3.1 The duplicate is gone: 6 rows in raw became 4 rows in bronze.
--     (5 distinct event_ids minus the 1 null-machine row that was quarantined.)
select
    (select count(*) from gea_demo.raw.raw_device_events    where event_date = date'2026-07-01') as raw_rows,
    (select count(*) from gea_demo.bronze.bronze_device_events where event_date = date'2026-07-01') as bronze_rows;
```

```sql
-- 3.2 Dedup rule made visible: bronze keeps the LATEST-ingested copy
--     (qualify row_number() ... order by source_ingested_at desc = 1),
--     so the surviving row is the 10:06:05 delivery, not the 10:01:05 one.
select event_id, machine_id, event_timestamp, source_ingested_at, _loaded_at
from gea_demo.bronze.bronze_device_events
where event_id = 'demo-0004';
```

```sql
-- 3.3 The malformed row never made it past bronze — 0 rows expected.
--     This is why the not_null test on bronze.machine_id passes because of the
--     transformation, not by luck.
select count(*) as null_machine_rows_in_bronze
from gea_demo.bronze.bronze_device_events
where machine_id is null;
```

```sql
-- 3.4 Fleet-wide version of the same story: the seed ships ~240 duplicate
--     event_ids and 25 null-machine rows; bronze absorbs all of them.
select
    (select count(*) from gea_demo.raw.raw_device_events)                                as raw_rows,
    (select count(distinct event_id) from gea_demo.raw.raw_device_events
      where machine_id is not null)                                                      as expected_bronze_rows,
    (select count(*) from gea_demo.bronze.bronze_device_events)                          as actual_bronze_rows;
```

```sql
-- 3.5 Incremental proof: run `dbt build --select bronze_device_events` again and
--     re-run this. _loaded_at gets NO new group, because the incremental filter
--     (event_timestamp > max(event_timestamp) in the target) matches nothing.
select _loaded_at, count(*) as rows_loaded_in_that_batch
from gea_demo.bronze.bronze_device_events
group by _loaded_at
order by _loaded_at desc
limit 5;
```

### Step 4 — Silver: conforming and historising

```sql
-- 4.1 silver_fact_device_events collapses the type-specific payload columns into
--     one generic `event_value`. For a vibration event, event_value = vibration_mm_s.
--     It also enriches with plant_location (from bronze_machines) and event_category
--     (from bronze_event_types) — the join that makes the fact business-ready.
select
    event_id, machine_id, plant_location, event_type_code, event_category,
    event_timestamp, vibration_mm_s, event_value
from gea_demo.silver.silver_fact_device_events
where machine_id = 'SLC-001'
  and event_date = date'2026-07-01'
order by event_timestamp;
```

```sql
-- 4.2 The same mapping across all event types — one column, many sources.
--     Shows why gold can ask for "min/max value in the bucket" without caring
--     which sensor produced the reading.
select
    event_type_code,
    count(*)                                                     as events,
    count(event_value)                                            as with_value,
    round(min(event_value), 2)                                    as min_value,
    round(max(event_value), 2)                                    as max_value
from gea_demo.silver.silver_fact_device_events
where machine_id = 'SLC-001'
group by event_type_code
order by event_type_code;
```

```sql
-- 4.3 SCD2 in silver_dim_machines: the machine's full status timeline, built from
--     sparse STATUS_CHANGE events with lead() over (partition by machine_id).
--     valid_to is the NEXT change's timestamp; the open-ended row is is_current.
select
    machine_sk, machine_id, status_value, valid_from, valid_to, is_current
from gea_demo.silver.silver_dim_machines
where machine_id = 'SLC-001'
order by valid_from;
```

```sql
-- 4.4 SCD2 invariants, checked by hand (dbt tests assert the same things):
--     exactly one current row per machine, and every row's valid_to equals the
--     next row's valid_from — no gaps, no overlaps.
select
    machine_id,
    count(*)                                                         as versions,
    sum(case when is_current then 1 else 0 end)                       as current_rows,
    sum(case when valid_to is not null
              and valid_to <> lead(valid_from) over (partition by machine_id order by valid_from)
             then 1 else 0 end)                                       as boundary_mismatches
from gea_demo.silver.silver_dim_machines
where machine_id = 'SLC-001'
group by machine_id;
```

```sql
-- 4.5 The payoff of SCD2: "what status was this machine in when the event fired?"
--     Point-in-time join on the [valid_from, valid_to) interval.
select
    f.event_id,
    f.event_timestamp,
    d.status_value as status_at_event_time,
    d.valid_from,
    d.valid_to
from gea_demo.silver.silver_fact_device_events f
join gea_demo.silver.silver_dim_machines d
  on d.machine_id = f.machine_id
 and f.event_timestamp >= d.valid_from
 and (f.event_timestamp < d.valid_to or d.valid_to is null)
where f.machine_id = 'SLC-001'
  and f.event_date = date'2026-07-01'
order by f.event_timestamp;
```

```sql
-- 4.6 The technical control table that drives the gold batch: one watermark row
--     per machine + event type. This is the state the gold model reads BEFORE
--     processing and advances AFTER processing.
select machine_id, event_type_code, last_processed_event_timestamp
from gea_demo.silver.silver_tec_watermark
where machine_id = 'SLC-001'
order by event_type_code;
```

### Step 5 — Gold: the targeted result

> **Read this before running Step 5.** `agg_event_frequency_minute` is a *view* whose
> WHERE clause is driven by `silver_tec_watermark`, and its post-hook advances that
> watermark from its own output. So immediately after a successful build, the view
> legitimately returns **zero rows for already-processed data** — that IS the
> incremental proof. To display results on stage, reset the watermark for the demo
> machine first (5.1), then query (5.2).

```sql
-- 5.1 Rewind the watermark for the demo machine only, so the view re-exposes
--     its slice. In production you would never do this — here it just makes the
--     incremental mechanism visible.
update gea_demo.silver.silver_tec_watermark
set last_processed_event_timestamp = timestamp'2026-06-30 23:59:59'
where machine_id = 'SLC-001'
  and event_type_code = 'SENSOR_VIBRATION_READING';
```

```sql
-- 5.2 The final gold result for our one minute bucket.
--     event_count = 4 (the duplicate was removed in bronze, the null-machine row
--     was quarantined), min value at 10:00:35 (1.20), max at 10:00:20 (4.80).
select *
from gea_demo.gold.agg_event_frequency_minute
where machine_id = 'SLC-001'
  and event_type_code = 'SENSOR_VIBRATION_READING'
  and bucket_start >= timestamp'2026-07-01 10:00:00'
order by bucket_start;
```

```sql
-- 5.3 Hand-verify the aggregate against silver — same numbers, computed the long
--     way. Great for the sceptic in the room.
with gapped as (
    select
        event_timestamp,
        event_value,
        datediff(second,
                 lag(event_timestamp) over (order by event_timestamp),
                 event_timestamp) as seconds_since_prev
    from gea_demo.silver.silver_fact_device_events
    where machine_id = 'SLC-001'
      and event_type_code = 'SENSOR_VIBRATION_READING'
      and event_timestamp >= timestamp'2026-07-01 10:00:00'
      and event_timestamp <  timestamp'2026-07-01 10:01:00'
)
select
    count(*)                    as event_count,
    min(event_timestamp)        as first_event_timestamp,
    max(event_timestamp)        as last_event_timestamp,
    avg(seconds_since_prev)     as avg_seconds_between_events
from gapped;
```

```sql
-- 5.4 Now re-run `dbt build --select agg_event_frequency_minute` and query again:
--     0 rows, because the post-hook already advanced the watermark past this batch.
--     Nothing is reprocessed — the whole point of the watermark pattern.
select count(*) as rows_still_pending
from gea_demo.gold.agg_event_frequency_minute
where machine_id = 'SLC-001'
  and event_type_code = 'SENSOR_VIBRATION_READING';
```

```sql
-- 5.5 The audit trail written by the log_batch_execution() post-hook: one row per
--     batch run, with row counts and duration. This is how you prove, after the
--     fact, what each run actually did.
select
    batch_run_id, model_name, row_count, distinct_machine_count,
    distinct_event_count, duration_seconds, run_started_at, run_completed_at
from gea_demo.silver.silver_tec_batch_execution_log
where model_name = 'agg_event_frequency_minute'
order by run_started_at desc
limit 5;
```

### Step 6 — Clean up the demo rows (optional)

```sql
-- 6.1 Remove the injected batch from raw so the repo returns to its seeded state.
delete from gea_demo.raw.raw_device_events where event_id like 'demo-%';
```

```bash
# 6.2 Rebuild the slice from scratch to restore a clean baseline.
dbt build --select +agg_event_frequency_minute --full-refresh
```

### Scenario cheat sheet

| Layer | What the audience sees | Query |
|---|---|---|
| raw | 6 rows land exactly as sent, dupes and nulls included | 1.2 / 1.3 |
| bronze | 6 → 4 rows: dedup keeps latest ingest, null machine quarantined | 3.1 / 3.2 / 3.3 |
| bronze | Second run processes nothing | 3.5 |
| silver fact | Payload columns conformed into one `event_value`, dims joined | 4.1 / 4.2 |
| silver dim | SCD2 timeline, one current row, point-in-time join | 4.3 / 4.4 / 4.5 |
| silver tec | Watermark state before/after the batch | 4.6 |
| gold | One minute bucket, counts and min/max timestamps | 5.2 / 5.3 |
| gold | Re-run is a genuine no-op; batch logged | 5.4 / 5.5 |

Slide Prompts (one-liners you can read)
-------------------------------------
- "dbt treats SQL as software: versioned, tested, documented, and modular."
- "Lineage and docs are first-class artifacts generated from the repo."
- "Selective builds let us run only the impacted part of the DAG in CI, saving cost and time."
- "Tests and SODA checks provide automated data-quality gates before deployment."
- "Incremental + merge strategies minimize work on re-runs — essential for large datasets."

Demo checklist (quick run during presentation)
-------------------------------------------
- [ ] `dbt seed` — show deterministic seeds
- [ ] `dbt build --select tag:bronze` — run incremental models
- [ ] `dbt test` — show test results
- [ ] `dbt build --select +silver_fact_device_events+` — show ++ selection
- [ ] `dbt docs generate && dbt docs serve` — open DAG and column docs
- [ ] Targeted scenario — inject the 6-row batch, `dbt build --select +agg_event_frequency_minute`, then walk queries 1.2 → 5.5

Optional advanced talking points
-------------------------------
- Snapshots for slowly-changing audit trails: `dbt snapshot`.
- Hooks and exposures to wire logging and external orchestration.
- Packages: share macros and tests across projects via `packages.yml` + `dbt deps`.
- Materializations: table, view, incremental, ephemeral — choose per tradeoffs.

Where to find this file
-----------------------
The demo guide lives at: [docs/dbt_presentation_demo.md](docs/dbt_presentation_demo.md)

Next steps I can do for you
--------------------------
- Add a short script to run the checklist and capture outputs (logs/screenshots).
- Create a short slide deck skeleton using these one-liners.
- Add example `requirements.txt` / runnable env setup for your presentation machine.
