from __future__ import annotations

from datetime import datetime, timezone
import json
from pathlib import Path

from environment.graph_builder import build_graph_from_scenario
from schemas.scenario import load_scenario_file
from simulation.kernel import run_turn_based_simulation
from simulation.log_writer import write_run_artifacts
from simulation.policy_trace import action_sequence_hash, summarize_action_counts, summarize_policy_metrics


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

    sequence_hash = action_sequence_hash(result)
    policy_summary = {
        "sequence_hash": sequence_hash,
        "action_counts": summarize_action_counts(result),
        "policy_metrics": summarize_policy_metrics(result),
    }

    policy_summary_path = Path(output_paths["run_dir"]) / "policy_summary.json"
    policy_summary_path.write_text(json.dumps(policy_summary, indent=2, sort_keys=True), encoding="utf-8")

    print("PHASE2_SMOKE_OK")
    print(f"timestamp_utc={datetime.now(timezone.utc).isoformat()}")
    print(f"scenario_id={scenario.metadata.scenario_id}")
    print(f"seed={seed}")
    print(f"horizon={horizon}")
    print(f"run_id={result.metadata.run_id}")
    print(f"sequence_hash={sequence_hash}")
    print(f"run_dir={output_paths['run_dir']}")
    print(f"policy_summary_file={policy_summary_path}")


if __name__ == "__main__":
    main()