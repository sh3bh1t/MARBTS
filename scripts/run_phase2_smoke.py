from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

from environment.graph_builder import build_graph_from_scenario
from metrics.baseline_metrics import write_baseline_metrics_artifact
from schemas.scenario import load_scenario_file
from simulation.kernel import run_turn_based_simulation
from simulation.log_writer import write_run_artifacts
from simulation.policy_trace import action_sequence_hash


def main() -> None:
    scenario_path = Path("scenarios/baselines/phase2_rule_baseline.json")
    scenario = load_scenario_file(scenario_path)
    graph = build_graph_from_scenario(scenario)

    seed = 20260329
    horizon = 8
    result = run_turn_based_simulation(
        graph,
        seed=seed,
        horizon=horizon,
        scenario_id=scenario.metadata.scenario_id,
    )

    artifacts_root = Path("artifacts/runs")
    output_paths = write_run_artifacts(result, artifacts_root)
    baseline_metrics_path = write_baseline_metrics_artifact(result, Path("artifacts/metrics"))

    sequence_hash = action_sequence_hash(result)

    print("PHASE2_SMOKE_OK")
    print(f"timestamp_utc={datetime.now(timezone.utc).isoformat()}")
    print(f"scenario_id={scenario.metadata.scenario_id}")
    print(f"seed={seed}")
    print(f"horizon={horizon}")
    print(f"run_id={result.metadata.run_id}")
    print(f"sequence_hash={sequence_hash}")
    print(f"run_dir={output_paths['run_dir']}")
    print(f"policy_metrics_file={output_paths['policy_metrics_file']}")
    print(f"baseline_metrics_file={baseline_metrics_path}")


if __name__ == "__main__":
    main()