from __future__ import annotations

from datetime import datetime, timezone

from schemas.catalog import build_scenario_catalog, select_latest_scenario_entries


def main() -> None:
    entries = build_scenario_catalog()
    latest_entries = select_latest_scenario_entries(entries)

    print("SCENARIO_CATALOG_SMOKE_OK")
    print(f"timestamp_utc={datetime.now(timezone.utc).isoformat()}")
    print(f"entry_count={len(entries)}")
    print(f"latest_entry_count={len(latest_entries)}")


if __name__ == "__main__":
    main()