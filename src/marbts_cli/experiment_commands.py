from __future__ import annotations

import argparse
from datetime import datetime, timezone
from pathlib import Path
from typing import Sequence

from experiments.ablation_report import run_ablation_report_package
from experiments.multi_seed_report import run_multi_seed_report
from experiments.policy_experiment_matrix import run_policy_experiment_matrix, run_policy_experiment_matrix_batch
from experiments.stress_test_suite import build_default_stress_test_configs, run_stress_test_suite
from hart.models import ExperimentPreset
from utils.runtime_presets import load_experiment_preset


DEFAULT_MULTI_SEED_PRESET = "configs/experiments/multi_seed_baseline.json"
DEFAULT_POLICY_MATRIX_PRESET = "configs/experiments/policy_experiment_matrix_baseline.json"
DEFAULT_STRESS_SUITE_PRESET = "configs/experiments/stress_test_suite_baseline.json"
DEFAULT_ABLATION_PRESET = "configs/experiments/ablation_report_baseline.json"

DEFAULT_MULTI_SEED_SCENARIO = "scenarios/baselines/rule_baseline.json"
DEFAULT_MULTI_SEED_SEEDS = [20260329, 20260330, 20260331]
DEFAULT_MULTI_SEED_HORIZON = 8

DEFAULT_POLICY_MATRIX_SCENARIO = "scenarios/baselines/rule_baseline.json"
DEFAULT_POLICY_MATRIX_SEEDS = [20260423, 20260424]
DEFAULT_POLICY_MATRIX_HORIZON = 2

DEFAULT_STRESS_SUITE_SEEDS = [20260423, 20260424]
DEFAULT_STRESS_SUITE_HORIZON = 3

DEFAULT_ABLATION_SCENARIO = "scenarios/baselines/rule_baseline.json"
DEFAULT_ABLATION_SEEDS = [20260423, 20260424]
DEFAULT_ABLATION_HORIZON = 2
DEFAULT_ABLATION_CONTAINER_IMAGE = "python:3.12-slim"
DEFAULT_ABLATION_CONTAINER_WORKDIR = "/workspace/MARBTS"

DEFAULT_RUNS_ROOT = "artifacts/runs"
DEFAULT_METRICS_ROOT = "artifacts/metrics"
DEFAULT_REPORTS_ROOT = "artifacts/reports"


def parse_seeds(raw_seeds: str) -> list[int]:
    seeds = [seed.strip() for seed in raw_seeds.split(",") if seed.strip()]
    if not seeds:
        raise ValueError("--seeds must include at least one integer value")
    try:
        return [int(seed) for seed in seeds]
    except ValueError as exc:
        raise ValueError("--seeds must be a comma-separated list of integers") from exc


def parse_scenario_batch(raw_scenarios: str) -> list[str]:
    scenario_paths = [scenario.strip() for scenario in raw_scenarios.split(",") if scenario.strip()]
    if not scenario_paths:
        raise ValueError("--scenario-batch must include at least one scenario path")
    return scenario_paths


def _coalesce(cli_value: str | int | None, preset_value: str | int | None, default_value: str | int) -> str | int:
    if cli_value is not None:
        return cli_value
    if preset_value is not None:
        return preset_value
    return default_value


def _load_preset(config_path: str) -> ExperimentPreset:
    return load_experiment_preset(config_path)


def _parse_multi_seed_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate a multi-seed aggregate report.",
    )
    parser.add_argument(
        "--config",
        default=DEFAULT_MULTI_SEED_PRESET,
        help="Path to experiment preset JSON.",
    )
    parser.add_argument(
        "--scenario",
        help="Path to scenario JSON file.",
    )
    parser.add_argument(
        "--seeds",
        help="Comma-separated integer seeds (e.g. 20260329,20260330).",
    )
    parser.add_argument(
        "--horizon",
        type=int,
        help="Simulation horizon per run.",
    )
    parser.add_argument(
        "--runs-root",
        help="Output root for run artifacts.",
    )
    parser.add_argument(
        "--metrics-root",
        help="Output root for baseline metrics artifacts.",
    )
    parser.add_argument(
        "--reports-root",
        help="Output root for aggregate report artifacts.",
    )
    return parser.parse_args(argv)


def run_multi_seed_report_main(argv: Sequence[str] | None = None) -> None:
    args = _parse_multi_seed_args(argv)
    preset = _load_preset(args.config)
    runtime = preset.runtime

    seeds = (
        parse_seeds(args.seeds)
        if args.seeds is not None
        else list(runtime.seeds or tuple(DEFAULT_MULTI_SEED_SEEDS))
    )

    output = run_multi_seed_report(
        scenario_path=Path(
            _coalesce(
                args.scenario,
                runtime.scenario_path,
                DEFAULT_MULTI_SEED_SCENARIO,
            )
        ),
        seeds=seeds,
        horizon=int(_coalesce(args.horizon, runtime.horizon, DEFAULT_MULTI_SEED_HORIZON)),
        runs_root=Path(_coalesce(args.runs_root, runtime.runs_root, DEFAULT_RUNS_ROOT)),
        metrics_root=Path(_coalesce(args.metrics_root, runtime.metrics_root, DEFAULT_METRICS_ROOT)),
        reports_root=Path(_coalesce(args.reports_root, runtime.reports_root, DEFAULT_REPORTS_ROOT)),
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


def _parse_policy_matrix_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate an adaptive-vs-rule policy experiment matrix report.",
    )
    parser.add_argument(
        "--config",
        default=DEFAULT_POLICY_MATRIX_PRESET,
        help="Path to experiment preset JSON.",
    )
    scenario_group = parser.add_mutually_exclusive_group()
    scenario_group.add_argument(
        "--scenario",
        help="Path to a single scenario JSON file.",
    )
    scenario_group.add_argument(
        "--scenario-batch",
        help="Comma-separated list of scenario JSON files to process as a batch.",
    )
    parser.add_argument(
        "--seeds",
        help="Comma-separated integer seeds (e.g. 20260423,20260424).",
    )
    parser.add_argument(
        "--horizon",
        type=int,
        help="Simulation horizon per run.",
    )
    parser.add_argument(
        "--runs-root",
        help="Output root for run artifacts.",
    )
    parser.add_argument(
        "--metrics-root",
        help="Output root for baseline metrics artifacts.",
    )
    parser.add_argument(
        "--reports-root",
        help="Output root for aggregate report artifacts.",
    )
    parser.add_argument(
        "--skip-ablations",
        action="store_true",
        help="Skip adaptive variant conditions (no-planning, reduced-observability, and decoy/bluff hooks).",
    )
    return parser.parse_args(argv)


def run_policy_experiment_matrix_main(argv: Sequence[str] | None = None) -> None:
    args = _parse_policy_matrix_args(argv)
    preset = _load_preset(args.config)
    runtime = preset.runtime
    include_ablations_default = True if preset.include_ablations is None else preset.include_ablations
    include_ablations = False if args.skip_ablations else include_ablations_default

    seeds = (
        parse_seeds(args.seeds)
        if args.seeds is not None
        else list(runtime.seeds or tuple(DEFAULT_POLICY_MATRIX_SEEDS))
    )
    horizon = int(_coalesce(args.horizon, runtime.horizon, DEFAULT_POLICY_MATRIX_HORIZON))
    runs_root = Path(_coalesce(args.runs_root, runtime.runs_root, DEFAULT_RUNS_ROOT))
    metrics_root = Path(_coalesce(args.metrics_root, runtime.metrics_root, DEFAULT_METRICS_ROOT))
    reports_root = Path(_coalesce(args.reports_root, runtime.reports_root, DEFAULT_REPORTS_ROOT))

    if args.scenario_batch is not None:
        scenario_batch = parse_scenario_batch(args.scenario_batch)
    elif runtime.scenario_batch:
        scenario_batch = list(runtime.scenario_batch)
    else:
        scenario_batch = []

    if args.scenario is not None:
        scenario_batch = []

    if scenario_batch:
        output = run_policy_experiment_matrix_batch(
            scenario_paths=scenario_batch,
            seeds=seeds,
            horizon=horizon,
            runs_root=runs_root,
            metrics_root=metrics_root,
            reports_root=reports_root,
            include_ablations=include_ablations,
        )
        metadata = output["report"]["batch_metadata"]
        print("POLICY_EXPERIMENT_MATRIX_BATCH_OK")
        print(f"timestamp_utc={datetime.now(timezone.utc).isoformat()}")
        print(f"scenario_count={metadata['scenario_count']}")
        print(f"seed_count={metadata['seed_count']}")
        print(f"horizon={metadata['horizon']}")
        print(f"include_ablations={metadata['include_ablations']}")
        print(f"report_file={output['report_file']}")
        return

    scenario_path = Path(
        _coalesce(
            args.scenario,
            runtime.scenario_path,
            DEFAULT_POLICY_MATRIX_SCENARIO,
        )
    )
    output = run_policy_experiment_matrix(
        scenario_path=scenario_path,
        seeds=seeds,
        horizon=horizon,
        runs_root=runs_root,
        metrics_root=metrics_root,
        reports_root=reports_root,
        include_ablations=include_ablations,
    )

    metadata = output["report"]["matrix_metadata"]
    print("POLICY_EXPERIMENT_MATRIX_OK")
    print(f"timestamp_utc={datetime.now(timezone.utc).isoformat()}")
    print(f"scenario_id={metadata['scenario_id']}")
    print(f"seed_count={metadata['seed_count']}")
    print(f"horizon={metadata['horizon']}")
    print(f"condition_count={metadata['condition_count']}")
    print(f"include_ablations={metadata['include_ablations']}")
    print(f"report_file={output['report_file']}")


def _parse_stress_suite_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate Phase 5 stress-test suite artifacts (scale/noise/observability).",
    )
    parser.add_argument(
        "--config",
        default=DEFAULT_STRESS_SUITE_PRESET,
        help="Path to experiment preset JSON.",
    )
    parser.add_argument(
        "--seeds",
        help="Comma-separated integer seeds (e.g. 20260423,20260424).",
    )
    parser.add_argument(
        "--horizon",
        type=int,
        help="Simulation horizon used by each stress profile.",
    )
    parser.add_argument(
        "--runs-root",
        help="Output root for run artifacts.",
    )
    parser.add_argument(
        "--metrics-root",
        help="Output root for baseline metrics artifacts.",
    )
    parser.add_argument(
        "--reports-root",
        help="Output root for aggregate report artifacts.",
    )
    return parser.parse_args(argv)


def run_stress_test_suite_main(argv: Sequence[str] | None = None) -> None:
    args = _parse_stress_suite_args(argv)
    preset = _load_preset(args.config)
    runtime = preset.runtime

    seeds = (
        parse_seeds(args.seeds)
        if args.seeds is not None
        else list(runtime.seeds or tuple(DEFAULT_STRESS_SUITE_SEEDS))
    )
    horizon = int(_coalesce(args.horizon, runtime.horizon, DEFAULT_STRESS_SUITE_HORIZON))
    profiles = build_default_stress_test_configs(seeds=tuple(seeds), horizon=horizon)

    output = run_stress_test_suite(
        profiles=profiles,
        runs_root=Path(_coalesce(args.runs_root, runtime.runs_root, DEFAULT_RUNS_ROOT)),
        metrics_root=Path(_coalesce(args.metrics_root, runtime.metrics_root, DEFAULT_METRICS_ROOT)),
        reports_root=Path(_coalesce(args.reports_root, runtime.reports_root, DEFAULT_REPORTS_ROOT)),
    )

    metadata = output["report"]["suite_metadata"]
    print("STRESS_TEST_SUITE_OK")
    print(f"timestamp_utc={datetime.now(timezone.utc).isoformat()}")
    print(f"profile_count={metadata['profile_count']}")
    print(f"profiles={','.join(metadata['profiles'])}")
    print(f"report_file={output['report_file']}")


def _parse_ablation_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate Phase 5 ablation report templates and optional container profile artifacts.",
    )
    parser.add_argument(
        "--config",
        default=DEFAULT_ABLATION_PRESET,
        help="Path to experiment preset JSON.",
    )
    parser.add_argument(
        "--scenario",
        help="Path to a single scenario JSON file.",
    )
    parser.add_argument(
        "--seeds",
        help="Comma-separated integer seeds (e.g. 20260423,20260424).",
    )
    parser.add_argument(
        "--horizon",
        type=int,
        help="Simulation horizon per run.",
    )
    parser.add_argument(
        "--runs-root",
        help="Output root for run artifacts.",
    )
    parser.add_argument(
        "--metrics-root",
        help="Output root for baseline metrics artifacts.",
    )
    parser.add_argument(
        "--reports-root",
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
        help="Container image to record in the optional execution profile.",
    )
    parser.add_argument(
        "--container-working-directory",
        help="Working directory to record in the optional execution profile.",
    )
    return parser.parse_args(argv)


def run_ablation_report_main(argv: Sequence[str] | None = None) -> None:
    args = _parse_ablation_args(argv)
    preset = _load_preset(args.config)
    runtime = preset.runtime

    seeds = (
        parse_seeds(args.seeds)
        if args.seeds is not None
        else list(runtime.seeds or tuple(DEFAULT_ABLATION_SEEDS))
    )
    include_ablations_default = True if preset.include_ablations is None else preset.include_ablations
    include_ablations = False if args.skip_ablations else include_ablations_default
    containerized = True if args.containerized else preset.containerized

    output = run_ablation_report_package(
        scenario_path=Path(_coalesce(args.scenario, runtime.scenario_path, DEFAULT_ABLATION_SCENARIO)),
        seeds=seeds,
        horizon=int(_coalesce(args.horizon, runtime.horizon, DEFAULT_ABLATION_HORIZON)),
        runs_root=Path(_coalesce(args.runs_root, runtime.runs_root, DEFAULT_RUNS_ROOT)),
        metrics_root=Path(_coalesce(args.metrics_root, runtime.metrics_root, DEFAULT_METRICS_ROOT)),
        reports_root=Path(_coalesce(args.reports_root, runtime.reports_root, DEFAULT_REPORTS_ROOT)),
        include_ablations=include_ablations,
        containerized=containerized,
        container_image=str(
            _coalesce(
                args.container_image,
                preset.container_image,
                DEFAULT_ABLATION_CONTAINER_IMAGE,
            )
        ),
        container_working_directory=str(
            _coalesce(
                args.container_working_directory,
                preset.container_working_directory,
                DEFAULT_ABLATION_CONTAINER_WORKDIR,
            )
        ),
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
