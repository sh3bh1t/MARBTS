from __future__ import annotations

import argparse
from datetime import datetime, timezone
from pathlib import Path

from experiments.stress_test_suite import build_default_stress_test_configs, run_stress_test_suite


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate Phase 5 stress-test suite artifacts (scale/noise/observability).",
    )
    parser.add_argument(
        "--seeds",
        default="20260423,20260424",
        help="Comma-separated integer seeds (e.g. 20260423,20260424).",
    )
    parser.add_argument(
        "--horizon",
        type=int,
        default=3,
        help="Simulation horizon used by each stress profile.",
    )
    parser.add_argument(
        "--runs-root",
        default="artifacts/runs",
        help="Output root for run artifacts.",
    )
    parser.add_argument(
        "--metrics-root",
        default="artifacts/metrics",
        help="Output root for baseline metrics artifacts.",
    )
    parser.add_argument(
        "--reports-root",
        default="artifacts/reports",
        help="Output root for aggregate report artifacts.",
    )
    return parser.parse_args()


def _parse_seeds(raw_seeds: str) -> tuple[int, ...]:
    seeds = [seed.strip() for seed in raw_seeds.split(",") if seed.strip()]
    if not seeds:
        raise ValueError("--seeds must include at least one integer value")
    try:
        return tuple(int(seed) for seed in seeds)
    except ValueError as exc:
        raise ValueError("--seeds must be a comma-separated list of integers") from exc


def main() -> None:
    args = _parse_args()
    seeds = _parse_seeds(args.seeds)
    profiles = build_default_stress_test_configs(seeds=seeds, horizon=args.horizon)

    output = run_stress_test_suite(
        profiles=profiles,
        runs_root=Path(args.runs_root),
        metrics_root=Path(args.metrics_root),
        reports_root=Path(args.reports_root),
    )

    metadata = output["report"]["suite_metadata"]
    print("STRESS_TEST_SUITE_OK")
    print(f"timestamp_utc={datetime.now(timezone.utc).isoformat()}")
    print(f"profile_count={metadata['profile_count']}")
    print(f"profiles={','.join(metadata['profiles'])}")
    print(f"report_file={output['report_file']}")


if __name__ == "__main__":
    main()
