#!/usr/bin/env python3
"""Run all SODA Core checks under tests/soda/checks/ against the Databricks
data source configured in tests/soda/configuration.yml.

Deliberately independent of dbt: run it any time after the relevant tables
exist (e.g. after `dbt build`), without needing a full dbt invocation:

    python tests/soda/scripts/run_soda_scan.py

Exits non-zero if any check fails or the scan itself errors, so it can gate
a CI pipeline the same way `dbt test` would.
"""
import sys
from pathlib import Path

from soda.scan import Scan

SODA_DIR = Path(__file__).resolve().parent.parent
CONFIG_PATH = SODA_DIR / "configuration.yml"
CHECKS_DIR = SODA_DIR / "checks"
DATA_SOURCE_NAME = "gea_demo"


def main() -> int:
    if not CONFIG_PATH.exists():
        print(f"Missing SODA configuration file: {CONFIG_PATH}")
        return 1

    check_files = sorted(CHECKS_DIR.glob("*.yml"))
    if not check_files:
        print(f"No check files found under {CHECKS_DIR}")
        return 1

    scan = Scan()
    scan.set_data_source_name(DATA_SOURCE_NAME)
    scan.add_configuration_yaml_file(str(CONFIG_PATH))

    for check_file in check_files:
        print(f"Adding checks from {check_file.name}")
        scan.add_sodacl_yaml_file(str(check_file))

    scan.set_verbose(True)
    scan.execute()

    print(scan.get_logs_text())

    if scan.has_error_logs():
        print("SODA scan ERRORED: see logs above.")
        return 1

    if scan.has_check_fails():
        print("SODA scan FAILED: one or more checks did not pass.")
        return 1

    print("SODA scan PASSED: all checks succeeded.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
