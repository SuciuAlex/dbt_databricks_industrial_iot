# GEA Industrial Telemetry — dbt-on-Databricks Showcase

A runnable demo repository showcasing the core architectural benefits of
**dbt** running on **Databricks**, using synthetic IoT telemetry from a
GEA-style industrial machine fleet (cooking, baking, slicing, packaging
equipment) as the business domain.

The full build specification lives in [`CLAUDE.md`](./CLAUDE.md) — this
README summarizes what the repo demonstrates and how to run it.

## What this demonstrates

1. A clean **raw → bronze → silver → gold** medallion architecture.
2. **`ref()`-only** model wiring — no hardcoded table names anywhere — so
   `dbt docs generate` produces a complete lineage graph from seeds all the
   way to gold.
3. **dbt tests** (`not_null`, `unique`, `relationships`, `accepted_values`,
   plus `dbt_utils`/`dbt_expectations` checks) at every layer.
4. **Incremental-only** materialization in bronze, modelled as append-only
   daily batch landings (one batch per `load_date`).
5. **SCD Type 2** history tracking in silver (`silver_dim_machines`), plus
   silver ownership of deduplication and quarantining.
6. **View-only** gold models that source exclusively from silver.
7. `dbt build --select +model_name+` rebuilding an exact upstream +
   downstream slice of the DAG.
8. A realistic watermark + KPI-mapping + batch-execution-log pattern
   powering three independent, incrementally-processed gold views.
9. A parallel **SODA** data-quality layer, independent of `dbt test`.
10. Five role-specific **agent skills** (`.claude/skills/`) covering the
    delivery lifecycle from ticket refinement through testing.

## Project layout

```
CLAUDE.md                  build specification / architecture source of truth
dbt_project.yml
packages.yml                dbt_utils, dbt_expectations
profiles.yml.example
.claude/skills/              5 role-specific agent skills
seeds/                       raw layer (4 CSVs, ~10.1k rows total)
models/raw/                  raw-layer exposure/doc (seeds ARE raw, no source())
models/bronze/                4 incremental models
models/silver/                3 business models (SCD2, facts) + 3 tec_ control tables
models/gold/                  10 views: dims, aggs, and the 3 event-frequency models
tests/                        singular dbt tests
tests/soda/                   independent SODA Core data-quality checks
macros/                       generate_schema_name, log_batch_execution
scripts/generate_synthetic_data.py
```

## Domain model

- **4 machine types** × **5 machines each** = 20 machines
  (`SLC-001..005`, `CKR-001..005`, `BKR-001..005`, `PKR-001..005`).
- **10 shared event types** (lifecycle/production/telemetry/fault/maintenance)
  emitted by every machine's gateway — payload columns are `NULL` where not
  applicable to a given event.
- **18 error codes** across LOW/MEDIUM/HIGH/CRITICAL severities.
- **~10,100 synthetic device events** over a 5-day window
  (2026-04-01 → 2026-04-05), generated deterministically (fixed seed) by
  `scripts/generate_synthetic_data.py`. Every event carries a `load_date`
  identifying which of the five simulated **daily load batches** delivered
  it, so the demo can replay one day at a time. The generator also injects
  intentional data-quality noise — ~2% of events are re-delivered in the
  *following* batch (duplicate `event_id`s with a later ingestion
  timestamp) and ~0.5% arrive with a null `machine_id` — which the **silver**
  layer is responsible for cleaning up.

## Layer responsibilities

- **Bronze** is a faithful, append-only landing zone: each run appends the
  incoming batch as-is. No deduplication, no filtering, no delta logic —
  re-running the same batch legitimately produces duplicates, exactly as a
  real raw landing zone would.
- **Silver** owns data quality: it quarantines rows with a null
  `machine_id`, deduplicates events by `event_id` (keeping the
  latest-ingested copy), deduplicates the re-appended dimension rows by
  `_loaded_at`, and builds the SCD2 machine dimension.
- **Gold** is views only, sourcing exclusively from silver.

## Setup

All four seed CSVs are committed (the fact seed is only ~10k rows), and are
fully reproducible from a fixed random seed if you want to regenerate them:

```bash
python3 -m pip install -r requirements.txt   # pandas/numpy for the data generator
python3 scripts/generate_synthetic_data.py   # regenerates seeds/*.csv deterministically

cp profiles.yml.example ~/.dbt/profiles.yml  # fill in your Databricks env vars:
export DBT_DATABRICKS_HOST=...
export DBT_DATABRICKS_HTTP_PATH=...
export DBT_DATABRICKS_TOKEN=...

dbt deps        # installs dbt_utils, dbt_expectations
dbt seed        # loads the raw layer
dbt build --threads 1   # builds + tests bronze -> silver -> gold end to end
```

> The three `agg_event_frequency_*` models each merge into the shared
> `silver_tec_watermark` table from a post-hook, so builds must run with
> `--threads 1` to avoid concurrent-write conflicts on Delta.

## The money-shot demos

```bash
# Full build, all layers, respecting the DAG
dbt build

# Rebuild everything upstream AND downstream of one silver model — shows
# dbt resolving the whole dependency chain from a single node. Good "hero
# nodes" for this: bronze_device_events (deep upstream fan-in from seeds)
# and silver_dim_machines (rich downstream fan-out to dim_machine_status,
# dim_machine_status_history, and agg_machine_uptime_daily).
dbt build --select +silver_dim_machines+

# Rebuild just the bronze layer and everything it feeds
dbt build --select bronze.* --select bronze.*+

# Layer-only builds via tags
dbt build --select tag:gold

# Rebuild only what changed since the last run (state-based, dbt Cloud/CI)
dbt build --select state:modified+
```

### Proof: simulating the five daily loads

Bronze models honour a `load_date` variable, so a single seed can be
replayed one batch at a time exactly as a daily scheduled job would:

```bash
dbt build --vars 'load_date: 2026-04-01' --threads 1
dbt build --vars 'load_date: 2026-04-02' --threads 1
# ... through 2026-04-05
```

Each run appends only that batch's rows to bronze. Running the same date
twice appends the batch twice — bronze is deliberately not idempotent,
mirroring a real landing zone — and silver's `event_id` dedup collapses the
duplicates away again, which is the point of the layer split. Omitting the
variable (`dbt build`) loads all five batches at once.

The three `agg_event_frequency_*` gold models show incrementality one layer
up: their watermark-driven read against `silver_tec_watermark` picks up
zero new rows on an unchanged second run, because their post-hooks already
advanced the watermark to the max processed timestamp on the first run.

### Proof: table and column comments land in Unity Catalog

`persist_docs` is enabled project-wide for relations and columns, so every
description written in the `.yml` files (all sourced from doc blocks in
`docs/`) is pushed into Databricks and is queryable after a build:

```sql
describe table extended gea_demo.silver.silver_fact_device_events;

select table_name, comment
from gea_demo.information_schema.tables
where table_schema in ('bronze', 'silver', 'gold');

select table_name, column_name, comment
from gea_demo.information_schema.columns
where table_schema in ('bronze', 'silver', 'gold');
```

## SODA data-quality layer

Independent of `dbt test`, and runnable without a full `dbt build`:

```bash
pip install soda-core-spark   # or the ODBC-flavored SODA Spark/Databricks package
python tests/soda/scripts/run_soda_scan.py
```

Checks live under `tests/soda/checks/` (`silver_dim_machines`,
`silver_fact_device_events`, `agg_event_frequency_*`) and cover invariants
that go a step beyond dbt's generic tests — no-overlapping-SCD2-periods as
a SQL-based check, `event_value` completeness by event type, freshness, and
bucket-window sanity on the event-frequency views.

## Docs / lineage

```bash
dbt docs generate
dbt docs serve
```

Renders the complete `raw seeds → bronze (4) → silver (6, incl. the 3
`tec_` control tables) → gold (10)` DAG, since every model is wired
exclusively through `ref()`.

## Agent skills (`.claude/skills/`)

Five role-specific playbooks for working this repo's delivery lifecycle,
each reaching its own conclusions independently rather than deferring to
another skill's output:

| Skill | Role |
|---|---|
| `data-architect-jira-refiner` | Turns vague asks into scoped, architecturally-sound tickets. |
| `jira-worker` | Works an assigned ticket end to end: implement, test, update, transition. |
| `data-engineer` | Implements dbt models/macros/tests per `CLAUDE.md`'s architecture. |
| `code-reviewer` | Reviews implementation PRs strictly on technical merit, independently. |
| `tester` | Hunts for edge cases upstream agents may have missed; owns `tests/soda/`. |
