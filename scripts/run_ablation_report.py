from __future__ import annotations

import argparse
from datetime import datetime, timezone
from pathlib import Path

from experiments.ablation_report import run_ablation_report_package


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate Phase 5 ablation report templates and optional container profile artifacts.",
    )
    parser.add_argument(
        "--scenario",
        default="scenarios/baselines/rule_baseline.json",
        help="Path to a single scenario JSON file.",
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
        help="Skip adaptive variant conditions in the source matrix.",
    )
    parser.add_argument(
        "--containerized",
        action="store_true",
        help="Emit an optional container execution profile alongside the report template.",
    )
    parser.add_argument(
        "--container-image",
        default="python:3.12-slim",
        help="Container image to record in the optional execution profile.",
    )
    parser.add_argument(
        "--container-working-directory",
        default="/workspace/MARBTS",
        help="Working directory to record in the optional execution profile.",
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
    seeds = _parse_seeds(args.seeds)

    output = run_ablation_report_package(
        scenario_path=Path(args.scenario),
        seeds=seeds,
        horizon=args.horizon,
        runs_root=Path(args.runs_root),
        metrics_root=Path(args.metrics_root),
        reports_root=Path(args.reports_root),
        include_ablations=not args.skip_ablations,
        containerized=args.containerized,
        container_image=args.container_image,
        container_working_directory=args.container_working_directory,
    )

    metadata = output["template"]["template_metadata"]
    print("ABLATION_REPORT_PACKAGE_OK")
    print(f"timestamp_utc={datetime.now(timezone.utc).isoformat()}")
    print(f"scenario_id={metadata['scenario_id']}")
    print(f"seed_count={metadata['seed_count']}")
    print(f"horizon={metadata['horizon']}")
    print(f"condition_count={metadata['condition_count']}")
    print(f"table_count={metadata['table_count']}")
    print(f"containerized={metadata['containerized']}")
    print(f"matrix_report_file={output['matrix_report_file']}")
    print(f"template_file={output['template_file']}")
    print(f"manifest_file={output['manifest_file']}")
    if output["container_profile_file"] is not None:
        print(f"container_profile_file={output['container_profile_file']}")


if __name__ == "__main__":
    main()