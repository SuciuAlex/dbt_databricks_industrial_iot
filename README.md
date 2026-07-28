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
4. **Incremental-only** materialization in bronze, with a genuine
   zero-new-rows no-op on a second run.
5. **SCD Type 2** history tracking in silver (`silver_dim_machines`).
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
seeds/                       raw layer (4 CSVs, ~801k rows total)
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
- **~801,000 synthetic device events** over a 3-month window
  (2026-04-01 → 2026-06-30), generated deterministically (fixed seed) by
  `scripts/generate_synthetic_data.py`, including a small amount of
  intentional data-quality noise (duplicate `event_id`s, null `machine_id`s)
  that `bronze_device_events` is responsible for cleaning up.

## Setup

`seeds/raw_device_events.csv` (~801k rows, ~100MB+) is **not committed** to
this repo — it's fully reproducible from a fixed random seed, and a file
that size is both a poor git citizen and over GitHub's 100MB per-file push
limit. The three small dimension seeds (`raw_machines`, `raw_event_types`,
`raw_error_codes`) are tiny and are committed as-is. Generate the fact seed
locally before `dbt seed`:

```bash
python3 -m pip install pandas numpy   # for the data generator
python3 scripts/generate_synthetic_data.py   # regenerates seeds/*.csv deterministically, incl. raw_device_events.csv

cp profiles.yml.example ~/.dbt/profiles.yml  # fill in your Databricks env vars:
export DBT_DATABRICKS_HOST=...
export DBT_DATABRICKS_HTTP_PATH=...
export DBT_DATABRICKS_TOKEN=...

dbt deps        # installs dbt_utils, dbt_expectations
dbt seed        # loads the raw layer
dbt build       # builds + tests bronze -> silver -> gold end to end
```

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

### Proof: incremental bronze does zero-row no-ops

Run `dbt build` a second time with no seed changes. Bronze's incremental
`merge` models process **zero new rows** — the `is_incremental()` filter on
`bronze_device_events` means nothing after `max(event_timestamp)` gets
rescanned, and the tiny dimension merges are no-ops on unchanged data. The
three `agg_event_frequency_*` gold models show the same story one layer up:
their watermark-driven read against `silver_tec_watermark` also picks up
zero new rows on an unchanged second run, because their post-hooks already
advanced the watermark to the max processed timestamp on the first run.

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
