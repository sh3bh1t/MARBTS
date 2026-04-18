from __future__ import annotations

from dataclasses import asdict
from datetime import datetime, timezone
import json
from pathlib import Path

from agents.adaptive import AdaptivePlanningPolicy
from agents.blue.rule_based import RuleBasedBluePolicy
from agents.interfaces.policy import PolicyRegistry
from agents.red.aggressive import AggressiveRedPolicy
from agents.red.rule_based import RuleBasedRedPolicy
from environment.graph_builder import build_graph_from_scenario
from hart.enums import ActorType
from hart.models import (
    AblationMatrix,
    AblationMatrixCondition,
    AdaptivePolicyConfig,
    PublicationMetricTable,
    ResearchArtifactManifest,
)
from metrics.baseline_metrics import compute_baseline_metrics
from schemas.scenario import load_scenario_file
from simulation.kernel import run_turn_based_simulation
from simulation.log_writer import write_run_artifacts


def load_ablation_matrix(path: str | Path) -> AblationMatrix:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("ablation matrix root must be an object")

    conditions_obj = payload.get("conditions")
    if not isinstance(conditions_obj, list) or not conditions_obj:
        raise ValueError("ablation matrix must contain a non-empty 'conditions' list")

    conditions = tuple(
        AblationMatrixCondition(
            condition_id=str(item["condition_id"]),
            red_mode=str(item["red_mode"]),
            blue_mode=str(item["blue_mode"]),
            feature_flags={str(key): bool(value) for key, value in dict(item.get("feature_flags", {})).items()},
        )
        for item in conditions_obj
    )
    return AblationMatrix(
        matrix_id=str(payload["matrix_id"]),
        scenario_id=str(payload["scenario_id"]),
        seeds=tuple(int(seed) for seed in payload["seeds"]),
        horizon=int(payload["horizon"]),
        planner_depth=int(payload.get("planner_depth", 3)),
        conditions=conditions,
    )


def _build_registry(condition: AblationMatrixCondition, planner_depth: int) -> PolicyRegistry:
    registry = PolicyRegistry()

    if condition.red_mode == "aggressive":
        registry.register(AggressiveRedPolicy())
    elif condition.red_mode == "rule_based":
        registry.register(RuleBasedRedPolicy())
    else:
        raise ValueError(f"unsupported red_mode '{condition.red_mode}'")

    if condition.blue_mode == "rule_based":
        registry.register(RuleBasedBluePolicy())
    elif condition.blue_mode == "adaptive":
        registry.register(
            AdaptivePlanningPolicy(
                ActorType.BLUE,
                AdaptivePolicyConfig(
                    backend="planning",
                    planning_depth=planner_depth,
                    feature_flags=dict(condition.feature_flags),
                ),
            )
        )
    else:
        raise ValueError(f"unsupported blue_mode '{condition.blue_mode}'")

    return registry


def _mean(values: list[float]) -> float:
    if not values:
        return 0.0
    return round(sum(values) / len(values), 3)


def run_phase5_ablation_suite(
    *,
    matrix_path: str | Path,
    scenario_path: str | Path,
    catalog_path: str | Path,
    runs_root: str | Path = "artifacts/runs",
    reports_root: str | Path = "artifacts/reports",
) -> dict:
    matrix = load_ablation_matrix(matrix_path)
    scenario = load_scenario_file(scenario_path)
    if scenario.metadata.scenario_id != matrix.scenario_id:
        raise ValueError(
            f"ablation matrix scenario mismatch: expected {matrix.scenario_id!r}, got {scenario.metadata.scenario_id!r}"
        )

    report_runs: list[dict] = []
    aggregates: list[dict] = []

    for condition in matrix.conditions:
        condition_metrics = {
            "final_compromised_nodes": [],
            "blue_deception_actions": [],
            "blue_decoy_actions": [],
            "blue_feint_actions": [],
            "deception_trigger_events": [],
        }
        for seed in matrix.seeds:
            graph = build_graph_from_scenario(scenario)
            result = run_turn_based_simulation(
                graph,
                seed=seed,
                horizon=matrix.horizon,
                scenario_id=scenario.metadata.scenario_id,
                scenario_version=scenario.metadata.version,
                config_payload={"scenario": asdict(scenario), "condition": asdict(condition)},
                policy_registry=_build_registry(condition, matrix.planner_depth),
            )
            artifacts = write_run_artifacts(result, runs_root)
            metrics = compute_baseline_metrics(result)
            security_outcomes = metrics["security_outcomes"]
            policy_performance = metrics["policy_performance"]
            condition_metrics["final_compromised_nodes"].append(int(security_outcomes["final_compromised_nodes"]))
            condition_metrics["blue_deception_actions"].append(int(policy_performance["blue_deception_actions"]))
            condition_metrics["blue_decoy_actions"].append(int(policy_performance["blue_decoy_actions"]))
            condition_metrics["blue_feint_actions"].append(int(policy_performance["blue_feint_actions"]))
            condition_metrics["deception_trigger_events"].append(int(policy_performance["deception_trigger_events"]))
            report_runs.append(
                {
                    "condition_id": condition.condition_id,
                    "seed": seed,
                    "red_mode": condition.red_mode,
                    "blue_mode": condition.blue_mode,
                    "feature_flags": dict(condition.feature_flags),
                    "run_id": result.metadata.run_id,
                    "run_dir": artifacts["run_dir"],
                    "final_compromised_nodes": int(security_outcomes["final_compromised_nodes"]),
                    "blue_deception_actions": int(policy_performance["blue_deception_actions"]),
                    "blue_decoy_actions": int(policy_performance["blue_decoy_actions"]),
                    "blue_feint_actions": int(policy_performance["blue_feint_actions"]),
                    "deception_trigger_events": int(policy_performance["deception_trigger_events"]),
                }
            )

        aggregates.append(
            {
                "condition_id": condition.condition_id,
                "red_mode": condition.red_mode,
                "blue_mode": condition.blue_mode,
                "feature_flags": dict(condition.feature_flags),
                "seed_count": len(matrix.seeds),
                "mean_final_compromised_nodes": _mean(condition_metrics["final_compromised_nodes"]),
                "mean_blue_deception_actions": _mean(condition_metrics["blue_deception_actions"]),
                "mean_blue_decoy_actions": _mean(condition_metrics["blue_decoy_actions"]),
                "mean_blue_feint_actions": _mean(condition_metrics["blue_feint_actions"]),
                "mean_deception_trigger_events": _mean(condition_metrics["deception_trigger_events"]),
                "min_final_compromised_nodes": min(condition_metrics["final_compromised_nodes"]),
                "max_final_compromised_nodes": max(condition_metrics["final_compromised_nodes"]),
            }
        )

    report_dir = Path(reports_root)
    report_dir.mkdir(parents=True, exist_ok=True)

    report_payload = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "matrix": asdict(matrix),
        "scenario_id": scenario.metadata.scenario_id,
        "scenario_version": scenario.metadata.version,
        "catalog_path": str(catalog_path),
        "aggregates": aggregates,
        "runs": report_runs,
    }
    report_file = report_dir / f"phase5_ablation_suite_{matrix.matrix_id}.json"
    report_file.write_text(json.dumps(report_payload, indent=2, sort_keys=True), encoding="utf-8")

    publication_table = PublicationMetricTable(
        table_id=f"{matrix.matrix_id}_summary",
        scenario_id=scenario.metadata.scenario_id,
        rows=tuple(
            {
                "condition_id": item["condition_id"],
                "mean_final_compromised_nodes": item["mean_final_compromised_nodes"],
                "mean_blue_decoy_actions": item["mean_blue_decoy_actions"],
                "mean_blue_feint_actions": item["mean_blue_feint_actions"],
                "mean_deception_trigger_events": item["mean_deception_trigger_events"],
            }
            for item in aggregates
        ),
    )
    publication_table_file = report_dir / f"phase5_publication_table_{matrix.matrix_id}.json"
    publication_table_file.write_text(json.dumps(asdict(publication_table), indent=2, sort_keys=True), encoding="utf-8")

    summary_lines = [
        f"# Phase 5 Ablation Summary: {matrix.matrix_id}",
        "",
        f"- Scenario: `{scenario.metadata.scenario_id}`",
        f"- Horizon: `{matrix.horizon}`",
        f"- Seeds: `{', '.join(str(seed) for seed in matrix.seeds)}`",
        "",
        "| Condition | Mean Final Compromise | Mean Decoy Actions | Mean Feint Actions | Mean Deception Triggers |",
        "| --- | ---: | ---: | ---: | ---: |",
    ]
    for item in aggregates:
        summary_lines.append(
            f"| `{item['condition_id']}` | {item['mean_final_compromised_nodes']} | "
            f"{item['mean_blue_decoy_actions']} | {item['mean_blue_feint_actions']} | "
            f"{item['mean_deception_trigger_events']} |"
        )
    summary_file = report_dir / f"phase5_ablation_suite_{matrix.matrix_id}.md"
    summary_file.write_text("\n".join(summary_lines) + "\n", encoding="utf-8")

    manifest = ResearchArtifactManifest(
        manifest_id=f"{matrix.matrix_id}_manifest",
        generated_at_utc=datetime.now(timezone.utc).isoformat(),
        report_files=(str(report_file), str(publication_table_file), str(summary_file)),
        config_files=(str(matrix_path), str(catalog_path)),
        scenario_catalog_path=str(catalog_path),
        notes=(
            "Phase 5 ablation suite bundle generated from deterministic seeded simulation runs.",
            "Publication table contains compact per-condition metrics intended for paper appendices.",
        ),
    )
    manifest_file = report_dir / f"phase5_manifest_{matrix.matrix_id}.json"
    manifest_file.write_text(json.dumps(asdict(manifest), indent=2, sort_keys=True), encoding="utf-8")

    return {
        "report_file": str(report_file),
        "publication_table_file": str(publication_table_file),
        "summary_file": str(summary_file),
        "manifest_file": str(manifest_file),
        "report": report_payload,
    }
