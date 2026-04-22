from __future__ import annotations

import argparse
from datetime import datetime, timezone
from pathlib import Path

from experiments.phase3_comparison import run_phase3_experiment_matrix


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate a Phase 3 adaptive-vs-rule experiment matrix report.",
    )
    parser.add_argument(
        "--scenario",
        default="scenarios/baselines/phase2_rule_baseline.json",
        help="Path to scenario JSON file.",
    )
    parser.add_argument(
        "--seeds",
        default="20260423,20260424",
        help="Comma-separated integer seeds (e.g. 20260423,20260424).",
    )
    parser.add_argument(
        "--horizon",
        type=int,
        default=2,
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
    parser.add_argument(
        "--skip-ablations",
        action="store_true",
        help="Skip no-planning and reduced-observability ablation conditions.",
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

    output = run_phase3_experiment_matrix(
        scenario_path=scenario_path,
        seeds=seeds,
        horizon=args.horizon,
        runs_root=Path(args.runs_root),
        metrics_root=Path(args.metrics_root),
        reports_root=Path(args.reports_root),
        include_ablations=not args.skip_ablations,
    )

    metadata = output["report"]["matrix_metadata"]
    print("PHASE3_MATRIX_REPORT_OK")
    print(f"timestamp_utc={datetime.now(timezone.utc).isoformat()}")
    print(f"scenario_id={metadata['scenario_id']}")
    print(f"seed_count={metadata['seed_count']}")
    print(f"horizon={metadata['horizon']}")
    print(f"condition_count={metadata['condition_count']}")
    print(f"include_ablations={metadata['include_ablations']}")
    print(f"report_file={output['report_file']}")


if __name__ == "__main__":
    main()