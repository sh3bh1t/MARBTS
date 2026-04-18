from __future__ import annotations

from collections.abc import Callable
from dataclasses import asdict
from datetime import datetime, timezone
import json
from pathlib import Path

from agents.adaptive import AdaptivePlanningPolicy, OpenAIAdaptivePolicy
from agents.blue.rule_based import RuleBasedBluePolicy
from agents.interfaces.policy import PolicyRegistry
from agents.red.rule_based import RuleBasedRedPolicy
from environment.graph_builder import build_graph_from_scenario
from hart.enums import ActorType
from hart.models import AblationConfig, AdaptivePolicyConfig, ComparisonMetricBundle, ExperimentCondition
from metrics.baseline_metrics import compute_baseline_metrics
from schemas.scenario import load_scenario_file
from simulation.kernel import run_turn_based_simulation
from simulation.log_writer import write_run_artifacts


def _merge_feature_flags(config: AdaptivePolicyConfig, ablation: AblationConfig) -> AdaptivePolicyConfig:
    feature_flags = dict(config.feature_flags)
    feature_flags["no_planning"] = ablation.no_planning
    feature_flags["reduced_observability"] = ablation.reduced_observability
    feature_flags["no_decoy"] = ablation.no_decoy
    feature_flags["no_feint"] = ablation.no_feint
    return AdaptivePolicyConfig(
        planning_depth=config.planning_depth,
        planning_mode=config.planning_mode,
        opponent_policy_name=config.opponent_policy_name,
        backend=config.backend,
        model_name=config.model_name,
        reasoning_effort=config.reasoning_effort,
        api_base_url=config.api_base_url,
        temperature=config.temperature,
        max_output_tokens=config.max_output_tokens,
        fallback_backend=config.fallback_backend,
        feature_flags=feature_flags,
    )


def _instantiate_policy(
    actor: ActorType,
    policy_name: str,
    adaptive_config: AdaptivePolicyConfig,
    client_factory: Callable[[], object] | None,
):
    if policy_name == "rule_based":
        return RuleBasedRedPolicy() if actor == ActorType.RED else RuleBasedBluePolicy()
    if policy_name == "planning":
        return AdaptivePlanningPolicy(actor, adaptive_config)
    if policy_name == "openai":
        return OpenAIAdaptivePolicy(actor, adaptive_config, client=client_factory() if client_factory else None)
    raise ValueError(f"unsupported policy_name '{policy_name}'")


def _build_registry(
    condition: ExperimentCondition,
    client_factory: Callable[[], object] | None,
) -> PolicyRegistry:
    registry = PolicyRegistry()
    adaptive_config = _merge_feature_flags(
        condition.adaptive_config or AdaptivePolicyConfig(),
        condition.ablation,
    )
    registry.register(_instantiate_policy(ActorType.RED, condition.red_policy, adaptive_config, client_factory))
    registry.register(_instantiate_policy(ActorType.BLUE, condition.blue_policy, adaptive_config, client_factory))
    return registry


def run_phase3_unified_comparison(
    *,
    scenario_path: str | Path,
    seeds: list[int],
    horizon: int,
    planner_config: AdaptivePolicyConfig | None = None,
    llm_config: AdaptivePolicyConfig | None = None,
    runs_root: str | Path = "artifacts/runs",
    reports_root: str | Path = "artifacts/reports",
    client_factory: Callable[[], object] | None = None,
) -> dict:
    if not seeds:
        raise ValueError("seeds cannot be empty")

    scenario = load_scenario_file(scenario_path)
    resolved_planner = planner_config or AdaptivePolicyConfig(backend="planning", planning_depth=3)
    resolved_llm = llm_config or AdaptivePolicyConfig(backend="openai", model_name="gpt-5-mini")

    conditions = [
        ExperimentCondition("rule_vs_rule", "rule_based", "rule_based"),
        ExperimentCondition("rule_vs_planner_blue", "rule_based", "planning", resolved_planner),
        ExperimentCondition("planner_red_vs_rule", "planning", "rule_based", resolved_planner),
        ExperimentCondition("rule_vs_llm_blue", "rule_based", "openai", resolved_llm),
        ExperimentCondition("llm_red_vs_rule", "openai", "rule_based", resolved_llm),
        ExperimentCondition(
            "rule_vs_planner_blue_no_planning",
            "rule_based",
            "planning",
            resolved_planner,
            AblationConfig(no_planning=True),
        ),
        ExperimentCondition(
            "rule_vs_planner_blue_reduced_observability",
            "rule_based",
            "planning",
            resolved_planner,
            AblationConfig(reduced_observability=True),
        ),
        ExperimentCondition(
            "rule_vs_llm_blue_reduced_observability",
            "rule_based",
            "openai",
            resolved_llm,
            AblationConfig(reduced_observability=True),
        ),
    ]

    per_run: list[dict] = []
    per_condition: dict[str, list[int]] = {}

    for condition in conditions:
        per_condition[condition.condition_id] = []
        for seed in seeds:
            graph = build_graph_from_scenario(scenario)
            result = run_turn_based_simulation(
                graph,
                seed=seed,
                horizon=horizon,
                scenario_id=scenario.metadata.scenario_id,
                scenario_version=scenario.metadata.version,
                config_payload=asdict(scenario),
                policy_registry=_build_registry(condition, client_factory),
            )
            artifacts = write_run_artifacts(result, runs_root)
            metrics = compute_baseline_metrics(result)
            final_compromised = int(metrics["security_outcomes"]["final_compromised_nodes"])
            per_condition[condition.condition_id].append(final_compromised)
            adaptive_config = condition.adaptive_config
            per_run.append(
                {
                    "condition_id": condition.condition_id,
                    "seed": seed,
                    "run_id": result.metadata.run_id,
                    "red_policy": condition.red_policy,
                    "blue_policy": condition.blue_policy,
                    "ablation": asdict(condition.ablation),
                    "adaptive_backend": adaptive_config.backend if adaptive_config else "none",
                    "model_name": adaptive_config.model_name if adaptive_config else "",
                    "planning_depth": adaptive_config.planning_depth if adaptive_config else 0,
                    "final_compromised_nodes": final_compromised,
                    "sequence_hash": metrics["sequence_hash"],
                    "run_dir": artifacts["run_dir"],
                }
            )

    aggregates: list[dict] = []
    for condition in conditions:
        values = per_condition[condition.condition_id]
        adaptive_config = condition.adaptive_config
        bundle = ComparisonMetricBundle(
            condition_id=condition.condition_id,
            seed_count=len(values),
            mean_final_compromised_nodes=round(sum(values) / len(values), 3),
            min_final_compromised_nodes=min(values),
            max_final_compromised_nodes=max(values),
        )
        aggregate = asdict(bundle)
        aggregate.update(
            {
                "red_policy": condition.red_policy,
                "blue_policy": condition.blue_policy,
                "ablation": asdict(condition.ablation),
            }
        )
        if adaptive_config is not None:
            aggregate["adaptive_backend"] = adaptive_config.backend
            aggregate["model_name"] = adaptive_config.model_name if adaptive_config.backend == "openai" else ""
            aggregate["reasoning_effort"] = adaptive_config.reasoning_effort if adaptive_config.backend == "openai" else ""
            aggregate["planning_depth"] = adaptive_config.planning_depth
        aggregates.append(aggregate)

    report_payload = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "scenario_id": scenario.metadata.scenario_id,
        "scenario_version": scenario.metadata.version,
        "horizon": horizon,
        "seed_count": len(seeds),
        "seeds": seeds,
        "planner_config": asdict(resolved_planner),
        "llm_config": asdict(resolved_llm),
        "aggregates": aggregates,
        "runs": per_run,
    }

    report_dir = Path(reports_root)
    report_dir.mkdir(parents=True, exist_ok=True)
    report_file = report_dir / f"phase3_unified_comparison_{scenario.metadata.scenario_id}.json"
    report_file.write_text(json.dumps(report_payload, indent=2, sort_keys=True), encoding="utf-8")
    return {"report_file": str(report_file), "report": report_payload}
