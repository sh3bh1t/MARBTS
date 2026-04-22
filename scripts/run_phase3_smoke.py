from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

from agents.adaptive import AdaptivePlanningPolicy
from agents.blue import RuleBasedBluePolicy
from agents.interfaces.policy import PolicyRegistry
from environment.graph_builder import build_graph_from_scenario
from hart.enums import ActorType
from hart.models import AdaptivePolicyConfig
from metrics.baseline_metrics import write_baseline_metrics_artifact
from schemas.scenario import load_scenario_file
from simulation.kernel import run_turn_based_simulation
from simulation.log_writer import write_run_artifacts
from simulation.policy_trace import action_sequence_hash


def main() -> None:
    scenario_path = Path("scenarios/baselines/phase2_rule_baseline.json")
    scenario = load_scenario_file(scenario_path)
    graph = build_graph_from_scenario(scenario)

    seed = 20260423
    horizon = 2
    adaptive_config = AdaptivePolicyConfig(planning_horizon=3, discount_factor=0.9, exploration_bias=0.0)

    policy_registry = PolicyRegistry()
    policy_registry.register(AdaptivePlanningPolicy(actor=ActorType.RED, config=adaptive_config))
    policy_registry.register(RuleBasedBluePolicy())

    result = run_turn_based_simulation(
        graph,
        seed=seed,
        horizon=horizon,
        scenario_id=f"{scenario.metadata.scenario_id}-phase3",
        policy_registry=policy_registry,
    )

    output_paths = write_run_artifacts(result, Path("artifacts/runs"))
    baseline_metrics_path = write_baseline_metrics_artifact(result, Path("artifacts/metrics"))

    sequence_hash = action_sequence_hash(result)

    print("PHASE3_SMOKE_OK")
    print(f"timestamp_utc={datetime.now(timezone.utc).isoformat()}")
    print(f"scenario_id={result.metadata.scenario_id}")
    print(f"seed={seed}")
    print(f"horizon={horizon}")
    print(f"run_id={result.metadata.run_id}")
    print(f"sequence_hash={sequence_hash}")
    print(f"run_dir={output_paths['run_dir']}")
    print(f"policy_metrics_file={output_paths['policy_metrics_file']}")
    print(f"baseline_metrics_file={baseline_metrics_path}")


if __name__ == "__main__":
    main()