from pathlib import Path
import re

root = Path(r'c:\_REPO\PoC\dbt_databricks_industrial_iot')
files = [
    root / 'models' / 'bronze' / 'bronze.yml',
    root / 'models' / 'silver' / 'silver.yml',
    root / 'models' / 'gold' / 'gold.yml',
    root / 'seeds' / 'seeds_properties.yml',
]
col_descs = {}

for path in files:
    text = path.read_text(encoding='utf-8')
    lines = text.splitlines()
    i = 0
    while i < len(lines):
        line = lines[i]
        m = re.match(r'^(\s*)- name: (.+)$', line)
        if m:
            indent = len(m.group(1))
            col = m.group(2).strip()
            j = i + 1
            while j < len(lines) and lines[j].strip() == '':
                j += 1
            if j < len(lines):
                desc_line = lines[j]
                md = re.match(r'^\s*description:\s*(>\s*)?(".*"|\'.*\'|.*)$', desc_line)
                if md:
                    if md.group(1):
                        # multi-line description block
                        desc_indent = len(re.match(r'^(\s*)', desc_line).group(1))
                        j += 1
                        desc_lines = []
                        while j < len(lines):
                            if lines[j].strip() == '':
                                desc_lines.append('')
                                j += 1
                                continue
                            cur_indent = len(re.match(r'^(\s*)', lines[j]).group(1))
                            if cur_indent > desc_indent:
                                desc_lines.append(lines[j].strip())
                                j += 1
                            else:
                                break
                        desc_text = ' '.join([x for x in desc_lines if x != ''])
                    else:
                        desc_text = md.group(2).strip().strip('"').strip("'")
                    if desc_text and col not in col_descs:
                        col_descs[col] = desc_text
        i += 1

# Add missing shared descriptions for fields that may not appear in the current files.
def add_if_missing(col, text):
    if col not in col_descs:
        col_descs[col] = text

add_if_missing('machine_sk', 'Surrogate key generated from machine_id and valid_from.')
add_if_missing('kpi_code', 'KPI mapping code currently defaulted to all.')
add_if_missing('batch_run_id', 'Unique batch execution identifier.')
add_if_missing('model_name', 'Name of the model that logged the batch.')
add_if_missing('row_count', 'Number of rows produced by the batch.')
add_if_missing('distinct_machine_count', 'Distinct machines processed in the batch.')
add_if_missing('distinct_event_count', 'Distinct event types processed in the batch.')
add_if_missing('duration_seconds', 'Execution duration of the batch in seconds.')
add_if_missing('run_started_at', 'Timestamp when the batch run started.')
add_if_missing('run_completed_at', 'Timestamp when the batch run completed.')
add_if_missing('status_since', 'Timestamp when this current status became active.')
add_if_missing('latest_temperature_c', 'Latest temperature reading value for the machine.')
add_if_missing('latest_temperature_at', 'Timestamp of the latest temperature reading.')
add_if_missing('latest_speed_units_per_min', 'Latest speed reading value for the machine.')
add_if_missing('latest_speed_at', 'Timestamp of the latest speed reading.')
add_if_missing('latest_vibration_mm_s', 'Latest vibration reading value for the machine.')
add_if_missing('latest_vibration_at', 'Timestamp of the latest vibration reading.')
add_if_missing('total_seconds', 'Total seconds of status overlap in the day.')
add_if_missing('running_seconds', 'Seconds RUNNING in the day.')
add_if_missing('down_seconds', 'Seconds in STOPPED/MAINTENANCE/ERROR.')
add_if_missing('idle_seconds', 'Seconds IDLE in the day.')
add_if_missing('pct_running', 'Percent of daily time in RUNNING.')
add_if_missing('pct_down', 'Percent of daily time in DOWN/ERROR/MAINTENANCE.')
add_if_missing('pct_idle', 'Percent of daily time in IDLE.')
add_if_missing('avg_temperature_c', 'Average temperature reading for the day.')
add_if_missing('avg_speed_units_per_min', 'Average speed reading for the day.')
add_if_missing('avg_vibration_mm_s', 'Average vibration reading for the day.')
add_if_missing('error_count', 'Count of errors.')
add_if_missing('avg_resolution_time_seconds', 'Average resolution time in seconds.')
add_if_missing('maintenance_required_count', 'Count of errors requiring maintenance.')
add_if_missing('total_product_count', 'Total product count for the day.')
add_if_missing('cycle_start_count', 'Count of cycle start events.')
add_if_missing('cycle_complete_count', 'Count of cycle complete events.')
add_if_missing('cycle_product_count', 'Total product count attributed to completed cycles.')
add_if_missing('avg_cycle_duration_seconds', 'Average duration of completed cycles in seconds.')
add_if_missing('bucket_start', 'Truncated bucket start timestamp for the bucket grain.')
add_if_missing('event_count', 'Number of events in the bucket.')
add_if_missing('first_event_timestamp', 'Timestamp of the first event in the bucket.')
add_if_missing('last_event_timestamp', 'Timestamp of the last event in the bucket.')
add_if_missing('timestamp_of_min_value', 'Event timestamp of the minimum payload value in the bucket.')
add_if_missing('timestamp_of_max_value', 'Event timestamp of the maximum payload value in the bucket.')
add_if_missing('avg_seconds_between_events', 'Average time between consecutive events in the bucket.')

# Write shared docs blocks to docs/column_documentation.md
blocks = []
for col in sorted(col_descs):
    blocks.append(f"{{% docs column_{col} %}}")
    blocks.append(col_descs[col])
    blocks.append("{% enddocs %}")
    blocks.append("")

(root / 'docs' / 'column_documentation.md').write_text('\n'.join(blocks).strip() + '\n', encoding='utf-8')

# Now rewrite schema files to use doc references
for path in files:
    text = path.read_text(encoding='utf-8')
    lines = text.splitlines()
    out = []
    i = 0
    while i < len(lines):
        line = lines[i]
        out.append(line)
        m = re.match(r'^(\s*)- name: (.+)$', line)
        if m:
            indent = len(m.group(1))
            col = m.group(2).strip()
            j = i + 1
            while j < len(lines) and lines[j].strip() == '':
                j += 1
            if j < len(lines) and re.match(r'^\s*description:\s*', lines[j]):
                desc_indent = len(re.match(r'^(\s*)', lines[j]).group(1))
                out.append(' ' * desc_indent + f'description: "{{{{ doc(\'column_{col}\') }}}}"')
                i = j + 1
                # skip multiline description block if present
                if '>' in lines[j] or '|' in lines[j]:
                    while i < len(lines):
                        cur_indent = len(re.match(r'^(\s*)', lines[i]).group(1))
                        if lines[i].strip() == '':
                            i += 1
                            continue
                        if cur_indent > desc_indent:
                            i += 1
                            continue
                        break
                # remove meta docs block immediately after description if present
                while i < len(lines) and re.match(r'^\s*meta:\s*$', lines[i]):
                    i += 1
                    while i < len(lines) and re.match(r'^\s*docs:\s*docs/column_documentation.md\s*$', lines[i]):
                        i += 1
                        break
                continue
        i += 1
    path.write_text('\n'.join(out) + ('\n' if text.endswith('\n') else ''), encoding='utf-8')

print('done')
