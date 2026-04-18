from __future__ import annotations

from collections.abc import Callable
from dataclasses import asdict
from datetime import datetime, timezone
import json
from pathlib import Path

from agents.adaptive import OpenAIAdaptivePolicy
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


def _build_registry(
    *,
    red_policy: str,
    blue_policy: str,
    llm_config: AdaptivePolicyConfig,
    client_factory: Callable[[], object] | None = None,
) -> PolicyRegistry:
    registry = PolicyRegistry()

    if red_policy == "llm":
        registry.register(
            OpenAIAdaptivePolicy(
                ActorType.RED,
                llm_config,
                client=client_factory() if client_factory is not None else None,
            )
        )
    else:
        registry.register(RuleBasedRedPolicy())

    if blue_policy == "llm":
        registry.register(
            OpenAIAdaptivePolicy(
                ActorType.BLUE,
                llm_config,
                client=client_factory() if client_factory is not None else None,
            )
        )
    else:
        registry.register(RuleBasedBluePolicy())

    return registry


def run_phase3_llm_comparison(
    *,
    scenario_path: str | Path,
    seeds: list[int],
    horizon: int,
    llm_config: AdaptivePolicyConfig | None = None,
    runs_root: str | Path = "artifacts/runs",
    reports_root: str | Path = "artifacts/reports",
    client_factory: Callable[[], object] | None = None,
) -> dict:
    if not seeds:
        raise ValueError("seeds cannot be empty")

    scenario = load_scenario_file(scenario_path)
    resolved_config = llm_config or AdaptivePolicyConfig(backend="openai")
    conditions = [
        {"condition_id": "rule_vs_rule", "red_policy": "rule_based", "blue_policy": "rule_based"},
        {"condition_id": "rule_vs_llm_blue", "red_policy": "rule_based", "blue_policy": "llm"},
        {"condition_id": "llm_red_vs_rule", "red_policy": "llm", "blue_policy": "rule_based"},
    ]

    per_run: list[dict] = []
    per_condition: dict[str, list[int]] = {}

    for condition in conditions:
        condition_id = condition["condition_id"]
        per_condition[condition_id] = []

        for seed in seeds:
            graph = build_graph_from_scenario(scenario)
            result = run_turn_based_simulation(
                graph,
                seed=seed,
                horizon=horizon,
                scenario_id=scenario.metadata.scenario_id,
                scenario_version=scenario.metadata.version,
                config_payload=asdict(scenario),
                policy_registry=_build_registry(
                    red_policy=condition["red_policy"],
                    blue_policy=condition["blue_policy"],
                    llm_config=resolved_config,
                    client_factory=client_factory,
                ),
            )
            artifacts = write_run_artifacts(result, runs_root)
            metrics = compute_baseline_metrics(result)
            final_compromised = int(metrics["security_outcomes"]["final_compromised_nodes"])
            per_condition[condition_id].append(final_compromised)
            per_run.append(
                {
                    "condition_id": condition_id,
                    "seed": seed,
                    "run_id": result.metadata.run_id,
                    "red_policy": condition["red_policy"],
                    "blue_policy": condition["blue_policy"],
                    "model_name": resolved_config.model_name,
                    "reasoning_effort": resolved_config.reasoning_effort,
                    "final_compromised_nodes": final_compromised,
                    "sequence_hash": metrics["sequence_hash"],
                    "run_dir": artifacts["run_dir"],
                }
            )

    aggregates = []
    for condition in conditions:
        condition_id = condition["condition_id"]
        values = per_condition[condition_id]
        aggregates.append(
            {
                "condition_id": condition_id,
                "red_policy": condition["red_policy"],
                "blue_policy": condition["blue_policy"],
                "model_name": resolved_config.model_name,
                "reasoning_effort": resolved_config.reasoning_effort,
                "seed_count": len(values),
                "mean_final_compromised_nodes": round(sum(values) / len(values), 3),
                "min_final_compromised_nodes": min(values),
                "max_final_compromised_nodes": max(values),
            }
        )

    report_payload = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "scenario_id": scenario.metadata.scenario_id,
        "scenario_version": scenario.metadata.version,
        "horizon": horizon,
        "seed_count": len(seeds),
        "seeds": seeds,
        "llm_config": asdict(resolved_config),
        "aggregates": aggregates,
        "runs": per_run,
    }

    report_dir = Path(reports_root)
    report_dir.mkdir(parents=True, exist_ok=True)
    report_file = report_dir / f"phase3_llm_comparison_{scenario.metadata.scenario_id}.json"
    report_file.write_text(json.dumps(report_payload, indent=2, sort_keys=True), encoding="utf-8")

    return {
        "report_file": str(report_file),
        "report": report_payload,
    }
