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
from hart.models import AdaptivePolicyConfig
from metrics.baseline_metrics import compute_baseline_metrics
from schemas.scenario import load_scenario_file
from simulation.kernel import run_turn_based_simulation
from simulation.log_writer import write_run_artifacts


def _build_registry(red_mode: str, blue_mode: str, planner_depth: int) -> PolicyRegistry:
    registry = PolicyRegistry()
    if red_mode == "aggressive":
        registry.register(AggressiveRedPolicy())
    elif red_mode == "rule_based":
        registry.register(RuleBasedRedPolicy())
    else:
        raise ValueError(f"unsupported red_mode '{red_mode}'")

    if blue_mode == "rule_based":
        registry.register(RuleBasedBluePolicy())
    elif blue_mode == "adaptive_decoy":
        registry.register(
            AdaptivePlanningPolicy(
                ActorType.BLUE,
                AdaptivePolicyConfig(
                    backend="planning",
                    planning_depth=planner_depth,
                    feature_flags={"no_decoy": False, "prefer_decoy": True},
                ),
            )
        )
    elif blue_mode == "adaptive_no_decoy":
        registry.register(
            AdaptivePlanningPolicy(
                ActorType.BLUE,
                AdaptivePolicyConfig(
                    backend="planning",
                    planning_depth=planner_depth,
                    feature_flags={"no_decoy": True},
                ),
            )
        )
    else:
        raise ValueError(f"unsupported blue_mode '{blue_mode}'")

    return registry


def run_phase5_decoy_efficacy(
    *,
    scenario_path: str | Path,
    seeds: list[int],
    horizon: int,
    planner_depth: int = 3,
    runs_root: str | Path = "artifacts/runs",
    reports_root: str | Path = "artifacts/reports",
) -> dict:
    if not seeds:
        raise ValueError("seeds cannot be empty")

    scenario = load_scenario_file(scenario_path)
    conditions = [
        {"condition_id": "rule_based_blue", "red_mode": "aggressive", "blue_mode": "rule_based"},
        {"condition_id": "adaptive_blue_with_decoy", "red_mode": "aggressive", "blue_mode": "adaptive_decoy"},
        {"condition_id": "adaptive_blue_without_decoy", "red_mode": "aggressive", "blue_mode": "adaptive_no_decoy"},
    ]

    per_run: list[dict] = []
    per_condition: dict[str, dict[str, list[float]]] = {}

    for condition in conditions:
        per_condition[condition["condition_id"]] = {
            "final_compromised_nodes": [],
            "blue_deception_actions": [],
            "deception_trigger_events": [],
        }
        for seed in seeds:
            graph = build_graph_from_scenario(scenario)
            result = run_turn_based_simulation(
                graph,
                seed=seed,
                horizon=horizon,
                scenario_id=scenario.metadata.scenario_id,
                scenario_version=scenario.metadata.version,
                config_payload=asdict(scenario),
                policy_registry=_build_registry(condition["red_mode"], condition["blue_mode"], planner_depth),
            )
            artifacts = write_run_artifacts(result, runs_root)
            metrics = compute_baseline_metrics(result)
            policy_performance = metrics["policy_performance"]
            final_compromised = int(metrics["security_outcomes"]["final_compromised_nodes"])
            deception_actions = int(policy_performance["blue_deception_actions"])
            deception_triggers = int(policy_performance["deception_trigger_events"])

            per_condition[condition["condition_id"]]["final_compromised_nodes"].append(final_compromised)
            per_condition[condition["condition_id"]]["blue_deception_actions"].append(deception_actions)
            per_condition[condition["condition_id"]]["deception_trigger_events"].append(deception_triggers)

            per_run.append(
                {
                    "condition_id": condition["condition_id"],
                    "seed": seed,
                    "red_mode": condition["red_mode"],
                    "blue_mode": condition["blue_mode"],
                    "run_id": result.metadata.run_id,
                    "final_compromised_nodes": final_compromised,
                    "blue_deception_actions": deception_actions,
                    "deception_trigger_events": deception_triggers,
                    "run_dir": artifacts["run_dir"],
                }
            )

    aggregates = []
    for condition in conditions:
        condition_id = condition["condition_id"]
        values = per_condition[condition_id]
        seed_count = len(values["final_compromised_nodes"])
        aggregates.append(
            {
                "condition_id": condition_id,
                "red_mode": condition["red_mode"],
                "blue_mode": condition["blue_mode"],
                "seed_count": seed_count,
                "mean_final_compromised_nodes": round(sum(values["final_compromised_nodes"]) / seed_count, 3),
                "mean_blue_deception_actions": round(sum(values["blue_deception_actions"]) / seed_count, 3),
                "mean_deception_trigger_events": round(sum(values["deception_trigger_events"]) / seed_count, 3),
                "min_final_compromised_nodes": min(values["final_compromised_nodes"]),
                "max_final_compromised_nodes": max(values["final_compromised_nodes"]),
            }
        )

    enabled = next(item for item in aggregates if item["condition_id"] == "adaptive_blue_with_decoy")
    disabled = next(item for item in aggregates if item["condition_id"] == "adaptive_blue_without_decoy")
    efficacy_observed = bool(
        enabled["mean_blue_deception_actions"] > 0 or enabled["mean_deception_trigger_events"] > 0
    )
    efficacy_summary = {
        "delta_final_compromised_nodes": round(
            disabled["mean_final_compromised_nodes"] - enabled["mean_final_compromised_nodes"],
            3,
        ),
        "delta_deception_trigger_events": round(
            enabled["mean_deception_trigger_events"] - disabled["mean_deception_trigger_events"],
            3,
        ),
        "efficacy_observed": efficacy_observed,
        "note": (
            "deception activity observed in decoy-enabled runs"
            if efficacy_observed
            else "no deception activity observed; use a higher-lateral-risk scenario or adjust policy heuristics"
        ),
    }

    report_payload = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "scenario_id": scenario.metadata.scenario_id,
        "scenario_version": scenario.metadata.version,
        "horizon": horizon,
        "seeds": seeds,
        "planner_depth": planner_depth,
        "aggregates": aggregates,
        "efficacy_summary": efficacy_summary,
        "runs": per_run,
    }

    report_dir = Path(reports_root)
    report_dir.mkdir(parents=True, exist_ok=True)
    report_file = report_dir / f"phase5_decoy_efficacy_{scenario.metadata.scenario_id}.json"
    report_file.write_text(json.dumps(report_payload, indent=2, sort_keys=True), encoding="utf-8")
    return {"report_file": str(report_file), "report": report_payload}
