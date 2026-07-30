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

Talking point: dbt docs serve exposes an interactive DAG (lineage), searchable column docs, and model descriptions. Use centralized `{% docs %}` blocks so multiple schema files reference the same descriptions.

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

8) Show documentation best-practice: centralized `{% docs %}`

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
