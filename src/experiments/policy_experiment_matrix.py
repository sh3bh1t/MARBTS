from __future__ import annotations

from dataclasses import asdict
from datetime import datetime, timezone
import json
from pathlib import Path
import statistics

from agents.adaptive import AdaptivePlanningPolicy
from agents.blue import RuleBasedBluePolicy
from agents.interfaces.policy import PolicyRegistry
from agents.red import RuleBasedRedPolicy
from environment.graph_builder import build_graph_from_scenario
from hart.enums import ActorType
from hart.models import AblationConfig, AdaptivePolicyConfig, ComparisonMetricBundle, ExperimentCondition
from metrics.baseline_metrics import compute_baseline_metrics, write_baseline_metrics_artifact
from schemas.scenario import load_scenario_file
from simulation.kernel import run_turn_based_simulation
from simulation.log_writer import write_run_artifacts


def _mean(values: list[float]) -> float:
    if not values:
        return 0.0
    return sum(values) / len(values)


def _stddev(values: list[float]) -> float:
    if len(values) < 2:
        return 0.0
    return statistics.pstdev(values)


def _build_adaptive_config(ablation: AblationConfig) -> AdaptivePolicyConfig:
    return AdaptivePolicyConfig(
        planning_horizon=1 if ablation.no_planning else 3,
        discount_factor=0.9,
        exploration_bias=0.0,
        reduced_observability=ablation.reduced_observability,
    )


def _build_conditions(*, seeds: list[int], horizon: int, include_ablations: bool) -> tuple[ExperimentCondition, ...]:
    conditions: list[ExperimentCondition] = [
        ExperimentCondition(
            condition_id="rule_red_vs_rule_blue",
            label="Rule Red vs Rule Blue",
            red_policy="rule",
            blue_policy="rule",
            seeds=tuple(seeds),
            horizon=horizon,
        ),
        ExperimentCondition(
            condition_id="adaptive_red_vs_rule_blue",
            label="Adaptive Red vs Rule Blue",
            red_policy="adaptive",
            blue_policy="rule",
            seeds=tuple(seeds),
            horizon=horizon,
            adaptive_config=_build_adaptive_config(AblationConfig()),
        ),
        ExperimentCondition(
            condition_id="rule_red_vs_adaptive_blue",
            label="Rule Red vs Adaptive Blue",
            red_policy="rule",
            blue_policy="adaptive",
            seeds=tuple(seeds),
            horizon=horizon,
            adaptive_config=_build_adaptive_config(AblationConfig()),
        ),
        ExperimentCondition(
            condition_id="adaptive_red_vs_adaptive_blue",
            label="Adaptive Red vs Adaptive Blue",
            red_policy="adaptive",
            blue_policy="adaptive",
            seeds=tuple(seeds),
            horizon=horizon,
            adaptive_config=_build_adaptive_config(AblationConfig()),
        ),
    ]

    if include_ablations:
        no_planning = AblationConfig(no_planning=True)
        reduced_observability = AblationConfig(reduced_observability=True)
        conditions.extend(
            (
                ExperimentCondition(
                    condition_id="adaptive_red_no_planning_vs_rule_blue",
                    label="Adaptive Red (No Planning) vs Rule Blue",
                    red_policy="adaptive",
                    blue_policy="rule",
                    seeds=tuple(seeds),
                    horizon=horizon,
                    ablation=no_planning,
                    adaptive_config=_build_adaptive_config(no_planning),
                ),
                ExperimentCondition(
                    condition_id="adaptive_red_reduced_observability_vs_rule_blue",
                    label="Adaptive Red (Reduced Observability) vs Rule Blue",
                    red_policy="adaptive",
                    blue_policy="rule",
                    seeds=tuple(seeds),
                    horizon=horizon,
                    ablation=reduced_observability,
                    adaptive_config=_build_adaptive_config(reduced_observability),
                ),
            )
        )

    return tuple(conditions)


def _build_policy_registry(condition: ExperimentCondition) -> PolicyRegistry:
    registry = PolicyRegistry()

    if condition.red_policy == "adaptive":
        adaptive_config = condition.adaptive_config or _build_adaptive_config(condition.ablation)
        registry.register(AdaptivePlanningPolicy(actor=ActorType.RED, config=adaptive_config))
    else:
        registry.register(RuleBasedRedPolicy())

    if condition.blue_policy == "adaptive":
        adaptive_config = condition.adaptive_config or _build_adaptive_config(condition.ablation)
        registry.register(AdaptivePlanningPolicy(actor=ActorType.BLUE, config=adaptive_config))
    else:
        registry.register(RuleBasedBluePolicy())

    return registry


def _aggregate_condition(condition: ExperimentCondition, runs: list[dict]) -> dict:
    final_compromised_values = [float(run["final_compromised_nodes"]) for run in runs]
    containment_timesteps = [
        float(run["first_containment_timestep"])
        for run in runs
        if run["first_containment_timestep"] >= 0
    ]
    blue_containment_values = [float(run["blue_containment_actions"]) for run in runs]
    sequence_hashes = [run["sequence_hash"] for run in runs]
    hash_frequency: dict[str, int] = {}
    for sequence_hash in sequence_hashes:
        hash_frequency[sequence_hash] = hash_frequency.get(sequence_hash, 0) + 1

    dominant_hash_count = max(hash_frequency.values()) if hash_frequency else 0
    deterministic_ratio = round((dominant_hash_count / len(runs)) if runs else 0.0, 3)
    metrics_bundle = ComparisonMetricBundle(
        condition_id=condition.condition_id,
        condition_label=condition.label,
        final_compromised_mean=round(_mean(final_compromised_values), 3),
        final_compromised_stddev=round(_stddev(final_compromised_values), 3),
        blue_containment_mean=round(_mean(blue_containment_values), 3),
        blue_containment_stddev=round(_stddev(blue_containment_values), 3),
        deterministic_consistency_ratio=deterministic_ratio,
    )

    return {
        "condition_id": condition.condition_id,
        "condition_label": condition.label,
        "red_policy": condition.red_policy,
        "blue_policy": condition.blue_policy,
        "ablation": asdict(condition.ablation),
        "adaptive_config": asdict(condition.adaptive_config) if condition.adaptive_config is not None else None,
        "run_count": len(runs),
        "metric_bundle": asdict(metrics_bundle),
        "first_containment_mean": round(_mean(containment_timesteps), 3) if containment_timesteps else -1,
        "first_containment_stddev": round(_stddev(containment_timesteps), 3) if containment_timesteps else -1,
        "sequence_hashes": sorted(hash_frequency.keys()),
        "hash_frequency": dict(sorted(hash_frequency.items())),
    }


def run_policy_experiment_matrix(
    *,
    scenario_path: str | Path,
    seeds: list[int],
    horizon: int,
    runs_root: str | Path = "artifacts/runs",
    metrics_root: str | Path = "artifacts/metrics",
    reports_root: str | Path = "artifacts/reports",
    include_ablations: bool = True,
) -> dict:
    if not seeds:
        raise ValueError("seeds cannot be empty")

    scenario = load_scenario_file(scenario_path)
    conditions = _build_conditions(seeds=seeds, horizon=horizon, include_ablations=include_ablations)
    all_runs: list[dict] = []
    runs_by_condition: dict[str, list[dict]] = {condition.condition_id: [] for condition in conditions}

    for condition in conditions:
        for seed in seeds:
            graph = build_graph_from_scenario(scenario)
            result = run_turn_based_simulation(
                graph,
                seed=seed,
                horizon=horizon,
                scenario_id=f"{scenario.metadata.scenario_id}:{condition.condition_id}",
                policy_registry=_build_policy_registry(condition),
            )

            run_artifacts = write_run_artifacts(result, runs_root)
            baseline_metrics_file = write_baseline_metrics_artifact(result, metrics_root)
            baseline_metrics = compute_baseline_metrics(result)

            run_record = {
                "condition_id": condition.condition_id,
                "condition_label": condition.label,
                "red_policy": condition.red_policy,
                "blue_policy": condition.blue_policy,
                "ablation": asdict(condition.ablation),
                "adaptive_config": asdict(condition.adaptive_config) if condition.adaptive_config is not None else None,
                "run_id": result.metadata.run_id,
                "seed": seed,
                "sequence_hash": baseline_metrics["sequence_hash"],
                "final_compromised_nodes": baseline_metrics["security_outcomes"]["final_compromised_nodes"],
                "first_containment_timestep": baseline_metrics["policy_performance"]["first_containment_timestep"],
                "blue_containment_actions": baseline_metrics["policy_performance"]["blue_containment_actions"],
                "run_dir": run_artifacts["run_dir"],
                "baseline_metrics_file": baseline_metrics_file,
            }
            all_runs.append(run_record)
            runs_by_condition[condition.condition_id].append(run_record)

    condition_aggregates = [_aggregate_condition(condition, runs_by_condition[condition.condition_id]) for condition in conditions]

    baseline_aggregate = next(
        (aggregate for aggregate in condition_aggregates if aggregate["condition_id"] == "rule_red_vs_rule_blue"),
        None,
    )
    baseline_final_compromised = (
        baseline_aggregate["metric_bundle"]["final_compromised_mean"]
        if baseline_aggregate is not None
        else 0.0
    )
    baseline_blue_containment = (
        baseline_aggregate["metric_bundle"]["blue_containment_mean"]
        if baseline_aggregate is not None
        else 0.0
    )

    comparison_to_baseline = []
    for aggregate in condition_aggregates:
        metric_bundle = aggregate["metric_bundle"]
        comparison_to_baseline.append(
            {
                "condition_id": aggregate["condition_id"],
                "condition_label": aggregate["condition_label"],
                "delta_final_compromised_mean_vs_rule_rule": round(
                    metric_bundle["final_compromised_mean"] - baseline_final_compromised,
                    3,
                ),
                "delta_blue_containment_mean_vs_rule_rule": round(
                    metric_bundle["blue_containment_mean"] - baseline_blue_containment,
                    3,
                ),
            }
        )

    report_payload = {
        "matrix_metadata": {
            "scenario_id": scenario.metadata.scenario_id,
            "scenario_version": scenario.metadata.version,
            "horizon": horizon,
            "seed_count": len(seeds),
            "seeds": seeds,
            "condition_count": len(conditions),
            "include_ablations": include_ablations,
            "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        },
        "conditions": [asdict(condition) for condition in conditions],
        "condition_aggregates": condition_aggregates,
        "comparison_to_baseline": comparison_to_baseline,
        "runs": all_runs,
    }

    report_dir = Path(reports_root)
    report_dir.mkdir(parents=True, exist_ok=True)
    report_file = report_dir / f"policy_experiment_matrix_{scenario.metadata.scenario_id}.json"
    report_file.write_text(json.dumps(report_payload, indent=2, sort_keys=True), encoding="utf-8")

    return {
        "report_file": str(report_file),
        "report": report_payload,
    }