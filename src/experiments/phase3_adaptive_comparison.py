from __future__ import annotations

from dataclasses import asdict
from datetime import datetime, timezone
import json
from pathlib import Path

from agents.adaptive import AdaptivePlanningPolicy
from agents.blue.rule_based import RuleBasedBluePolicy
from agents.interfaces.policy import PolicyRegistry
from agents.red.rule_based import RuleBasedRedPolicy
from environment.graph_builder import build_graph_from_scenario
from hart.enums import ActorType
from hart.models import AdaptivePolicyConfig
from metrics.baseline_metrics import compute_baseline_metrics
from schemas.scenario import load_scenario_file
from simulation.kernel import run_turn_based_simulation
from simulation.log_writer import write_run_artifacts


def _build_registry(red_policy: str, blue_policy: str, planning_depth: int) -> PolicyRegistry:
    registry = PolicyRegistry()

    if red_policy == "adaptive":
        registry.register(AdaptivePlanningPolicy(ActorType.RED, AdaptivePolicyConfig(planning_depth=planning_depth)))
    else:
        registry.register(RuleBasedRedPolicy())

    if blue_policy == "adaptive":
        registry.register(AdaptivePlanningPolicy(ActorType.BLUE, AdaptivePolicyConfig(planning_depth=planning_depth)))
    else:
        registry.register(RuleBasedBluePolicy())

    return registry


def run_phase3_adaptive_comparison(
    *,
    scenario_path: str | Path,
    seeds: list[int],
    horizon: int,
    planning_depth: int = 3,
    runs_root: str | Path = "artifacts/runs",
    reports_root: str | Path = "artifacts/reports",
) -> dict:
    if not seeds:
        raise ValueError("seeds cannot be empty")

    scenario = load_scenario_file(scenario_path)
    conditions = [
        {"condition_id": "rule_vs_rule", "red_policy": "rule_based", "blue_policy": "rule_based"},
        {"condition_id": "rule_vs_adaptive_blue", "red_policy": "rule_based", "blue_policy": "adaptive"},
        {"condition_id": "adaptive_red_vs_rule", "red_policy": "adaptive", "blue_policy": "rule_based"},
        {"condition_id": "adaptive_vs_adaptive", "red_policy": "adaptive", "blue_policy": "adaptive"},
        {"condition_id": "adaptive_blue_ablation_depth1", "red_policy": "rule_based", "blue_policy": "adaptive", "planning_depth": 1},
    ]

    per_run: list[dict] = []
    per_condition: dict[str, list[int]] = {}

    for condition in conditions:
        condition_id = condition["condition_id"]
        per_condition[condition_id] = []
        condition_depth = int(condition.get("planning_depth", planning_depth))

        for seed in seeds:
            graph = build_graph_from_scenario(scenario)
            result = run_turn_based_simulation(
                graph,
                seed=seed,
                horizon=horizon,
                scenario_id=scenario.metadata.scenario_id,
                scenario_version=scenario.metadata.version,
                config_payload=asdict(scenario),
                policy_registry=_build_registry(condition["red_policy"], condition["blue_policy"], condition_depth),
            )
            artifacts = write_run_artifacts(result, runs_root)
            metrics = compute_baseline_metrics(result)
            final_compromised = int(metrics["security_outcomes"]["final_compromised_nodes"])
            per_condition[condition_id].append(final_compromised)

            per_run.append(
                {
                    "condition_id": condition_id,
                    "seed": seed,
                    "planning_depth": condition_depth,
                    "red_policy": condition["red_policy"],
                    "blue_policy": condition["blue_policy"],
                    "run_id": result.metadata.run_id,
                    "final_compromised_nodes": final_compromised,
                    "sequence_hash": metrics["sequence_hash"],
                    "run_dir": artifacts["run_dir"],
                }
            )

    aggregates = []
    for condition in conditions:
        condition_id = condition["condition_id"]
        compromised_values = per_condition[condition_id]
        aggregates.append(
            {
                "condition_id": condition_id,
                "red_policy": condition["red_policy"],
                "blue_policy": condition["blue_policy"],
                "planning_depth": int(condition.get("planning_depth", planning_depth)),
                "seed_count": len(compromised_values),
                "mean_final_compromised_nodes": round(sum(compromised_values) / len(compromised_values), 3),
                "min_final_compromised_nodes": min(compromised_values),
                "max_final_compromised_nodes": max(compromised_values),
            }
        )

    report_payload = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "scenario_id": scenario.metadata.scenario_id,
        "scenario_version": scenario.metadata.version,
        "horizon": horizon,
        "seed_count": len(seeds),
        "seeds": seeds,
        "aggregates": aggregates,
        "runs": per_run,
    }

    report_dir = Path(reports_root)
    report_dir.mkdir(parents=True, exist_ok=True)
    report_file = report_dir / f"phase3_adaptive_comparison_{scenario.metadata.scenario_id}.json"
    report_file.write_text(json.dumps(report_payload, indent=2, sort_keys=True), encoding="utf-8")

    return {
        "report_file": str(report_file),
        "report": report_payload,
    }
