from __future__ import annotations

import json
from pathlib import Path
import tempfile

from environment.graph_builder import build_graph_from_scenario
from schemas.scenario import load_scenario_file
from simulation.kernel import run_turn_based_simulation
from simulation.log_writer import write_run_artifacts
from simulation.policy_trace import action_sequence_hash


def test_policy_metrics_artifact_matches_simulation_trace() -> None:
    scenario = load_scenario_file("scenarios/baselines/rule_baseline.json")
    graph = build_graph_from_scenario(scenario)
    result = run_turn_based_simulation(
        graph,
        seed=20260329,
        horizon=8,
        scenario_id=scenario.metadata.scenario_id,
    )

    with tempfile.TemporaryDirectory() as temp_dir:
        paths = write_run_artifacts(result, temp_dir)
        policy_metrics_path = Path(paths["policy_metrics_file"])
        payload = json.loads(policy_metrics_path.read_text(encoding="utf-8"))

    assert payload["run_id"] == result.metadata.run_id
    assert payload["scenario_id"] == scenario.metadata.scenario_id
    assert payload["sequence_hash"] == action_sequence_hash(result)
    assert payload["action_counts"]["red"]
    assert payload["action_counts"]["blue"]
    assert "red" in payload["policy_metrics"]
    assert "blue" in payload["policy_metrics"]