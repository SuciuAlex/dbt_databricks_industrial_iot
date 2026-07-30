"""Query the built gea_demo tables on Databricks and dump readable result snippets.

Used to source the real query output embedded in docs/dbt_databricks_presentation.pdf.
Requires DBT_DATABRICKS_HOST / _HTTP_PATH / _TOKEN in the environment.
"""

import os
import sys

from databricks import sql

QUERIES = [
    (
        "Row counts by layer",
        """
        select 'raw.raw_device_events' as object, count(*) as rows from gea_demo.raw.raw_device_events
        union all select 'bronze.bronze_device_events', count(*) from gea_demo.bronze.bronze_device_events
        union all select 'silver.silver_fact_device_events', count(*) from gea_demo.silver.silver_fact_device_events
        union all select 'silver.silver_dim_machines', count(*) from gea_demo.silver.silver_dim_machines
        union all select 'silver.silver_fact_error_events', count(*) from gea_demo.silver.silver_fact_error_events
        """,
    ),
    (
        "silver.silver_tec_batch_execution_log",
        """
        select model_name, row_count, distinct_machine_count as machines,
               distinct_event_count as events, duration_seconds
        from gea_demo.silver.silver_tec_batch_execution_log
        order by run_started_at, model_name
        """,
    ),
    (
        "gold.dim_machine_status sample",
        """
        select machine_id, machine_type, status_value, plant_location,
               firmware_version, status_since
        from gea_demo.gold.dim_machine_status
        order by machine_id limit 6
        """,
    ),
    (
        "gold.agg_machine_uptime_daily sample",
        """
        select machine_id, event_date, round(pct_running, 1) as pct_running,
               round(pct_down, 1) as pct_down, round(pct_idle, 1) as pct_idle
        from gea_demo.gold.agg_machine_uptime_daily
        order by event_date desc, machine_id limit 6
        """,
    ),
    (
        "gold.agg_error_analysis sample",
        """
        select machine_type, severity, error_count,
               round(avg_resolution_time_seconds, 0) as avg_resolution_s,
               maintenance_required_count
        from gea_demo.gold.agg_error_analysis
        order by error_count desc limit 6
        """,
    ),
]


def render(columns, rows):
    header = [str(c) for c in columns]
    body = [[("" if v is None else str(v)) for v in r] for r in rows]
    widths = [max(len(header[i]), *(len(r[i]) for r in body)) if body else len(header[i])
              for i in range(len(header))]
    out = ["  ".join(h.ljust(w) for h, w in zip(header, widths)).rstrip()]
    out += ["  ".join(v.ljust(w) for v, w in zip(r, widths)).rstrip() for r in body]
    return "\n".join(out)


def main():
    conn = sql.connect(
        server_hostname=os.environ["DBT_DATABRICKS_HOST"],
        http_path=os.environ["DBT_DATABRICKS_HTTP_PATH"],
        access_token=os.environ["DBT_DATABRICKS_TOKEN"],
    )
    blocks = []
    with conn.cursor() as cur:
        for title, query in QUERIES:
            cur.execute(query)
            rows = cur.fetchall()
            columns = [d[0] for d in cur.description]
            blocks.append(f"== {title} ==\n{render(columns, rows)}\n")
    conn.close()

    text = "\n".join(blocks)
    os.makedirs("logs", exist_ok=True)
    with open("logs/db_query_results.txt", "w", encoding="utf-8") as fh:
        fh.write(text)
    sys.stdout.write(text)


if __name__ == "__main__":
    main()
