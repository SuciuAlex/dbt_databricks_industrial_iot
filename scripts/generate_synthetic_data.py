#!/usr/bin/env python3
"""Generate synthetic GEA industrial telemetry seed data.

Produces the four raw seed CSVs under seeds/ per CLAUDE.md section 3:
raw_machines, raw_event_types, raw_error_codes, raw_device_events.

Deterministic: uses a fixed numpy Generator seed so re-running produces
byte-identical output. Run with: python scripts/generate_synthetic_data.py
"""
import uuid
from pathlib import Path

import numpy as np
import pandas as pd

SEED = 42
rng = np.random.default_rng(SEED)

REPO_ROOT = Path(__file__).resolve().parent.parent
SEEDS_DIR = REPO_ROOT / "seeds"

START_DATE = pd.Timestamp("2026-04-01")
END_DATE = pd.Timestamp("2026-06-30")
N_DAYS = (END_DATE - START_DATE).days + 1  # 91 days, "exactly 3 months"

MAX_TOTAL_ROWS = 1_000_000
N_DENSE_EVENTS_PER_MACHINE = 40_000  # tuned to land total volume in the 700k-850k range

# ---------------------------------------------------------------------------
# Reference data
# ---------------------------------------------------------------------------

MACHINE_TYPES = ["SLICER", "COOKER", "BAKER", "PACKER"]
TYPE_PREFIX = {"SLICER": "SLC", "COOKER": "CKR", "BAKER": "BKR", "PACKER": "PKR"}
MACHINES_PER_TYPE = 5

MODEL_NAMES = {
    "SLICER": ["CutMaster 3000", "CutMaster Pro", "SlicePro X2"],
    "COOKER": ["ThermoCook 500", "CookMaster Elite", "ThermoCook XL"],
    "BAKER": ["BakeMaster 200", "OvenPro Industrial", "BakeMaster XL"],
    "PACKER": ["PackLine 400", "SealPro Auto", "PackLine XL"],
}

CAPACITY_UNITS = {
    "SLICER": "kg/min",
    "COOKER": "liters/batch",
    "BAKER": "units/hour",
    "PACKER": "units/min",
}
RATED_CAPACITY_RANGE = {
    "SLICER": (80, 220),
    "COOKER": (200, 800),
    "BAKER": (500, 2000),
    "PACKER": (60, 180),
}

PLANTS = [
    ("Cologne", "Germany"),
    ("Bologna", "Italy"),
    ("Chicago", "USA"),
    ("Sao Paulo", "Brazil"),
    ("Melbourne", "Australia"),
    ("Shanghai", "China"),
]

EVENT_TYPES = [
    ("STATUS_CHANGE", "lifecycle", "Machine transitions between RUNNING, IDLE, STOPPED, MAINTENANCE, ERROR", False),
    ("CYCLE_START", "production", "A production/process cycle begins", False),
    ("CYCLE_COMPLETE", "production", "A production/process cycle ends, with cycle duration", True),
    ("SENSOR_TEMPERATURE_READING", "telemetry", "Core temperature reading (deg C)", True),
    ("SENSOR_SPEED_READING", "telemetry", "Line/blade speed (units/min)", True),
    ("SENSOR_VIBRATION_READING", "telemetry", "Vibration amplitude (mm/s)", True),
    ("PRODUCT_COUNT_UPDATE", "production", "Running output counter increment", True),
    ("ERROR_RAISED", "fault", "Fault raised, references error_code", False),
    ("ERROR_RESOLVED", "fault", "Fault cleared, references error_code", False),
    ("MAINTENANCE_ALERT", "maintenance", "Preventive/predictive maintenance flag", False),
]

ERROR_CODES = [
    ("E-101", "HIGH", "Blade misalignment", True),
    ("E-110", "MEDIUM", "Blade dull/worn", True),
    ("E-120", "HIGH", "Cutting motor overload", True),
    ("E-204", "MEDIUM", "Oven temperature deviation", False),
    ("E-210", "HIGH", "Oven ignition failure", True),
    ("E-220", "CRITICAL", "Heating element failure", True),
    ("E-310", "MEDIUM", "Conveyor jam", False),
    ("E-320", "HIGH", "Conveyor motor fault", True),
    ("E-330", "LOW", "Conveyor belt slippage", False),
    ("E-401", "LOW", "Sensor calibration drift", False),
    ("E-410", "MEDIUM", "Sensor communication loss", True),
    ("E-450", "MEDIUM", "Packaging seal failure", False),
    ("E-460", "LOW", "Packaging film jam", False),
    ("E-470", "LOW", "Label applicator fault", False),
    ("E-500", "CRITICAL", "Emergency stop triggered", True),
    ("E-510", "HIGH", "Power supply fluctuation", True),
    ("E-520", "HIGH", "Hydraulic pressure loss", True),
    ("E-600", "LOW", "Software watchdog reset", False),
]

# Sensor bias per machine type: (mean, std, clip_lo, clip_hi)
TEMP_PARAMS = {
    "COOKER": (170.0, 25.0, 120.0, 220.0),
    "BAKER": (160.0, 20.0, 120.0, 220.0),
    "SLICER": (35.0, 8.0, 15.0, 60.0),
    "PACKER": (40.0, 8.0, 15.0, 60.0),
}
SPEED_PARAMS = {
    "SLICER": (85.0, 15.0),
    "PACKER": (70.0, 12.0),
    "COOKER": (20.0, 5.0),
    "BAKER": (15.0, 5.0),
}
VIBRATION_PARAMS = {
    "SLICER": (4.5, 1.2),
    "PACKER": (3.0, 0.8),
    "COOKER": (1.5, 0.5),
    "BAKER": (1.2, 0.4),
}
CYCLE_DURATION_RANGE_SECONDS = {
    "SLICER": (30, 300),
    "COOKER": (300, 3600),
    "BAKER": (600, 5400),
    "PACKER": (20, 240),
}

DENSE_EVENT_TYPES = np.array(
    [
        "SENSOR_TEMPERATURE_READING",
        "SENSOR_SPEED_READING",
        "SENSOR_VIBRATION_READING",
        "PRODUCT_COUNT_UPDATE",
        "CYCLE_START",
        "CYCLE_COMPLETE",
    ]
)
DENSE_EVENT_WEIGHTS = np.array([0.20, 0.20, 0.20, 0.25, 0.075, 0.075])

STATUS_CYCLE = ["RUNNING", "IDLE", "RUNNING", "MAINTENANCE", "RUNNING", "ERROR", "RUNNING", "STOPPED"]

SEVERITY_DELAY_MINUTES = {
    "LOW": (5, 30),
    "MEDIUM": (30, 180),
    "HIGH": (60, 480),
    "CRITICAL": (240, 1440),
}

EMPTY_PAYLOAD_COLS = [
    "status_value",
    "temperature_c",
    "speed_units_per_min",
    "vibration_mm_s",
    "product_count",
    "cycle_duration_seconds",
    "error_code",
]

# ---------------------------------------------------------------------------
# Diurnal / weekly weighting
# ---------------------------------------------------------------------------

_dates = [START_DATE + pd.Timedelta(days=i) for i in range(N_DAYS)]
_dow = np.array([d.dayofweek for d in _dates])
DAY_WEIGHTS = np.where(_dow < 5, 1.0, 0.4)
DAY_WEIGHTS = DAY_WEIGHTS / DAY_WEIGHTS.sum()

_hours = np.arange(24)
HOUR_WEIGHTS = np.where((_hours >= 6) & (_hours <= 21), 1.0, 0.15)
HOUR_WEIGHTS = HOUR_WEIGHTS / HOUR_WEIGHTS.sum()


def sample_time_components(n, rng):
    day_idx = rng.choice(N_DAYS, size=n, p=DAY_WEIGHTS)
    hour = rng.choice(24, size=n, p=HOUR_WEIGHTS)
    minute = rng.integers(0, 60, size=n)
    second = rng.integers(0, 60, size=n)
    ts = (
        START_DATE
        + pd.to_timedelta(day_idx, unit="D")
        + pd.to_timedelta(hour, unit="h")
        + pd.to_timedelta(minute, unit="m")
        + pd.to_timedelta(second, unit="s")
    )
    return day_idx, pd.DatetimeIndex(ts)


# ---------------------------------------------------------------------------
# Dimension seeds
# ---------------------------------------------------------------------------


def build_machines():
    rows = []
    for t_idx, machine_type in enumerate(MACHINE_TYPES):
        for seq in range(1, MACHINES_PER_TYPE + 1):
            machine_id = f"{TYPE_PREFIX[machine_type]}-{seq:03d}"
            plant = PLANTS[(t_idx * MACHINES_PER_TYPE + seq) % len(PLANTS)]
            install_offset_days = int(rng.integers(200, 3600))
            install_date = START_DATE - pd.Timedelta(days=install_offset_days)
            cap_lo, cap_hi = RATED_CAPACITY_RANGE[machine_type]
            rows.append(
                {
                    "machine_id": machine_id,
                    "machine_type": machine_type,
                    "model_name": MODEL_NAMES[machine_type][(seq - 1) % len(MODEL_NAMES[machine_type])],
                    "manufacturer": "GEA Group",
                    "plant_location": plant[0],
                    "plant_country": plant[1],
                    "install_date": install_date.date().isoformat(),
                    "rated_capacity": round(float(rng.uniform(cap_lo, cap_hi)), 1),
                    "capacity_unit": CAPACITY_UNITS[machine_type],
                    "initial_firmware_version": f"v{rng.integers(1,5)}.{rng.integers(0,10)}.{rng.integers(0,21)}",
                }
            )
    return pd.DataFrame(rows)


def build_event_types():
    return pd.DataFrame(
        EVENT_TYPES, columns=["event_type_code", "event_category", "description", "has_numeric_payload"]
    )


def build_error_codes():
    return pd.DataFrame(ERROR_CODES, columns=["error_code", "severity", "description", "requires_maintenance"])


# ---------------------------------------------------------------------------
# Fact seed: raw_device_events
# ---------------------------------------------------------------------------


def generate_dense_events_for_machine(machine_id, machine_type):
    n = N_DENSE_EVENTS_PER_MACHINE
    day_idx, ts = sample_time_components(n, rng)
    event_type = rng.choice(DENSE_EVENT_TYPES, size=n, p=DENSE_EVENT_WEIGHTS)

    df = pd.DataFrame(
        {
            "machine_id": machine_id,
            "machine_type": machine_type,
            "event_type_code": event_type,
            "event_timestamp": ts,
        }
    )

    temp_mean, temp_std, temp_lo, temp_hi = TEMP_PARAMS[machine_type]
    speed_mean, speed_std = SPEED_PARAMS[machine_type]
    vib_mean, vib_std = VIBRATION_PARAMS[machine_type]
    cyc_lo, cyc_hi = CYCLE_DURATION_RANGE_SECONDS[machine_type]

    temperature_c = np.full(n, np.nan)
    speed_units_per_min = np.full(n, np.nan)
    vibration_mm_s = np.full(n, np.nan)
    product_count = np.full(n, np.nan)
    cycle_duration_seconds = np.full(n, np.nan)

    is_temp = event_type == "SENSOR_TEMPERATURE_READING"
    is_speed = event_type == "SENSOR_SPEED_READING"
    is_vib = event_type == "SENSOR_VIBRATION_READING"
    is_prod = event_type == "PRODUCT_COUNT_UPDATE"
    is_cc = event_type == "CYCLE_COMPLETE"

    n_temp = int(is_temp.sum())
    if n_temp:
        drift = temp_std * 0.4 * np.sin(2 * np.pi * day_idx[is_temp] / 45.0)
        vals = rng.normal(temp_mean, temp_std * 0.5, size=n_temp) + drift
        temperature_c[is_temp] = np.clip(vals, temp_lo, temp_hi)

    n_speed = int(is_speed.sum())
    if n_speed:
        vals = rng.normal(speed_mean, speed_std, size=n_speed)
        speed_units_per_min[is_speed] = np.clip(vals, 0, None)

    n_vib = int(is_vib.sum())
    if n_vib:
        vals = rng.normal(vib_mean, vib_std, size=n_vib)
        vibration_mm_s[is_vib] = np.clip(vals, 0, None)

    n_prod = int(is_prod.sum())
    if n_prod:
        product_count[is_prod] = rng.integers(1, 51, size=n_prod)

    n_cc = int(is_cc.sum())
    if n_cc:
        product_count[is_cc] = rng.integers(50, 501, size=n_cc)
        cycle_duration_seconds[is_cc] = rng.integers(cyc_lo, cyc_hi + 1, size=n_cc)

    df["status_value"] = None
    df["temperature_c"] = np.round(temperature_c, 2)
    df["speed_units_per_min"] = np.round(speed_units_per_min, 2)
    df["vibration_mm_s"] = np.round(vibration_mm_s, 3)
    df["product_count"] = product_count
    df["cycle_duration_seconds"] = cycle_duration_seconds
    df["error_code"] = None
    return df


def generate_status_changes_for_machine(machine_id, machine_type):
    n = int(rng.integers(15, 31))
    _, ts = sample_time_components(n, rng)
    ts_sorted = ts.sort_values()
    status_values = [STATUS_CYCLE[i % len(STATUS_CYCLE)] for i in range(n)]

    df = pd.DataFrame(
        {
            "machine_id": machine_id,
            "machine_type": machine_type,
            "event_type_code": "STATUS_CHANGE",
            "event_timestamp": ts_sorted,
            "status_value": status_values,
        }
    )
    for col in [c for c in EMPTY_PAYLOAD_COLS if c != "status_value"]:
        df[col] = None
    return df


def generate_error_episodes_for_machine(machine_id, machine_type, error_codes_df):
    n_episodes = int(rng.integers(3, 8))
    _, raised_ts = sample_time_components(n_episodes, rng)
    idxs = rng.integers(0, len(error_codes_df), size=n_episodes)
    codes = error_codes_df.iloc[idxs].reset_index(drop=True)

    rows = []
    for i in range(n_episodes):
        code = codes.loc[i, "error_code"]
        severity = codes.loc[i, "severity"]
        lo, hi = SEVERITY_DELAY_MINUTES[severity]
        delay_min = int(rng.integers(lo, hi + 1))
        resolved_ts = raised_ts[i] + pd.Timedelta(minutes=delay_min)
        max_ts = END_DATE + pd.Timedelta(hours=23, minutes=59, seconds=59)
        if resolved_ts > max_ts:
            resolved_ts = max_ts
        rows.append({"event_timestamp": raised_ts[i], "event_type_code": "ERROR_RAISED", "error_code": code})
        rows.append({"event_timestamp": resolved_ts, "event_type_code": "ERROR_RESOLVED", "error_code": code})

    df = pd.DataFrame(rows)
    df["machine_id"] = machine_id
    df["machine_type"] = machine_type
    for col in [c for c in EMPTY_PAYLOAD_COLS if c != "error_code"]:
        df[col] = None
    return df


def generate_maintenance_alerts_for_machine(machine_id, machine_type, maintenance_ts):
    rows = []
    for t in maintenance_ts:
        if rng.random() < 0.7:
            lead_hours = int(rng.integers(1, 49))
            alert_ts = t - pd.Timedelta(hours=lead_hours)
            if alert_ts < START_DATE:
                alert_ts = START_DATE + pd.Timedelta(hours=1)
            rows.append({"event_timestamp": alert_ts})

    n_extra = int(rng.integers(0, 3))
    if n_extra:
        _, extra_ts = sample_time_components(n_extra, rng)
        rows.extend({"event_timestamp": t} for t in extra_ts)

    if not rows:
        cols = ["machine_id", "machine_type", "event_type_code", "event_timestamp"] + EMPTY_PAYLOAD_COLS
        return pd.DataFrame(columns=cols)

    df = pd.DataFrame(rows)
    df["machine_id"] = machine_id
    df["machine_type"] = machine_type
    df["event_type_code"] = "MAINTENANCE_ALERT"
    for col in EMPTY_PAYLOAD_COLS:
        df[col] = None
    return df


def build_device_events(machines_df, error_codes_df):
    machine_frames = []
    for _, machine in machines_df.iterrows():
        machine_id = machine["machine_id"]
        machine_type = machine["machine_type"]

        dense = generate_dense_events_for_machine(machine_id, machine_type)
        status = generate_status_changes_for_machine(machine_id, machine_type)
        errors = generate_error_episodes_for_machine(machine_id, machine_type, error_codes_df)
        maintenance_ts = status.loc[status["status_value"] == "MAINTENANCE", "event_timestamp"]
        maintenance = generate_maintenance_alerts_for_machine(machine_id, machine_type, maintenance_ts)

        machine_frames.append(pd.concat([dense, status, errors, maintenance], ignore_index=True))

    df = pd.concat(machine_frames, ignore_index=True)
    df["event_timestamp"] = pd.to_datetime(df["event_timestamp"])

    # source_ingested_at: small ingestion lag, occasional stragglers
    n = len(df)
    lag_seconds = rng.integers(0, 121, size=n)
    straggler = rng.random(n) < 0.03
    lag_seconds = np.where(straggler, rng.integers(300, 3600, size=n), lag_seconds)
    df["source_ingested_at"] = df["event_timestamp"] + pd.to_timedelta(lag_seconds, unit="s")

    # event_id: deterministic pseudo-UUIDv4 from the seeded generator
    raw_bytes = rng.integers(0, 256, size=(n, 16), dtype=np.uint8)
    df["event_id"] = [str(uuid.UUID(bytes=bytes(row), version=4)) for row in raw_bytes]

    # --- intentional data quality noise (cleaned up in bronze) ---
    n_dupe = max(1, int(n * 0.0003))  # well under the 0.05% cap
    dupe_idx = rng.choice(n, size=n_dupe, replace=False)
    dupes = df.iloc[dupe_idx].copy()
    dupes["source_ingested_at"] = dupes["source_ingested_at"] + pd.to_timedelta(
        rng.integers(30, 600, size=n_dupe), unit="s"
    )
    df = pd.concat([df, dupes], ignore_index=True)

    n_null_machine = 25
    null_idx = rng.choice(len(df), size=n_null_machine, replace=False)
    df.loc[null_idx, "machine_id"] = None

    # shuffle to mimic mixed-arrival ingestion order
    shuffle_idx = rng.permutation(len(df))
    df = df.iloc[shuffle_idx].reset_index(drop=True)

    df["event_date"] = df["event_timestamp"].dt.date
    df["product_count"] = df["product_count"].astype("Int64")
    df["cycle_duration_seconds"] = df["cycle_duration_seconds"].astype("Int64")

    column_order = [
        "event_id",
        "machine_id",
        "machine_type",
        "event_type_code",
        "event_timestamp",
        "event_date",
        "status_value",
        "temperature_c",
        "speed_units_per_min",
        "vibration_mm_s",
        "product_count",
        "cycle_duration_seconds",
        "error_code",
        "source_ingested_at",
    ]
    return df[column_order]


def main():
    SEEDS_DIR.mkdir(parents=True, exist_ok=True)

    machines_df = build_machines()
    event_types_df = build_event_types()
    error_codes_df = build_error_codes()
    device_events_df = build_device_events(machines_df, error_codes_df)

    machines_df.to_csv(SEEDS_DIR / "raw_machines.csv", index=False)
    event_types_df.to_csv(SEEDS_DIR / "raw_event_types.csv", index=False)
    error_codes_df.to_csv(SEEDS_DIR / "raw_error_codes.csv", index=False)
    device_events_df.to_csv(SEEDS_DIR / "raw_device_events.csv", index=False)

    counts = {
        "raw_machines.csv": len(machines_df),
        "raw_event_types.csv": len(event_types_df),
        "raw_error_codes.csv": len(error_codes_df),
        "raw_device_events.csv": len(device_events_df),
    }
    total = sum(counts.values())

    print("Generated seed row counts:")
    for name, count in counts.items():
        print(f"  {name}: {count:,}")
    print(f"  TOTAL: {total:,}")

    assert total < MAX_TOTAL_ROWS, f"Total row count {total:,} exceeds the {MAX_TOTAL_ROWS:,} cap"
    print(f"OK: total row count is under the {MAX_TOTAL_ROWS:,} row cap.")


if __name__ == "__main__":
    main()
