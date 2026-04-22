from __future__ import annotations

import argparse
from datetime import datetime, timezone
from pathlib import Path

from experiments.multi_seed_report import run_multi_seed_report


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate a multi-seed aggregate report.",
    )
    parser.add_argument(
        "--scenario",
        default="scenarios/baselines/rule_baseline.json",
        help="Path to scenario JSON file.",
    )
    parser.add_argument(
        "--seeds",
        default="20260329,20260330,20260331",
        help="Comma-separated integer seeds (e.g. 20260329,20260330).",
    )
    parser.add_argument(
        "--horizon",
        type=int,
        default=8,
        help="Simulation horizon per run.",
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


def _parse_seeds(raw_seeds: str) -> list[int]:
    seeds = [seed.strip() for seed in raw_seeds.split(",") if seed.strip()]
    if not seeds:
        raise ValueError("--seeds must include at least one integer value")
    try:
        return [int(seed) for seed in seeds]
    except ValueError as exc:
        raise ValueError("--seeds must be a comma-separated list of integers") from exc


def main() -> None:
    args = _parse_args()
    scenario_path = Path(args.scenario)
    seeds = _parse_seeds(args.seeds)
    horizon = args.horizon

    output = run_multi_seed_report(
        scenario_path=scenario_path,
        seeds=seeds,
        horizon=horizon,
        runs_root=Path(args.runs_root),
        metrics_root=Path(args.metrics_root),
        reports_root=Path(args.reports_root),
    )

    aggregate = output["report"]["aggregate"]
    print("MULTI_SEED_REPORT_OK")
    print(f"timestamp_utc={datetime.now(timezone.utc).isoformat()}")
    print(f"scenario_id={aggregate['scenario_id']}")
    print(f"seed_count={aggregate['seed_count']}")
    print(f"horizon={aggregate['horizon']}")
    print(f"final_compromised_mean={aggregate['final_compromised_mean']}")
    print(f"deterministic_consistency_ratio={aggregate['deterministic_consistency_ratio']}")
    print(f"report_file={output['report_file']}")


if __name__ == "__main__":
    main()