from __future__ import annotations

import json
from pathlib import Path
import tempfile

from environment.graph_builder import build_graph_from_scenario
from metrics.baseline_metrics import compute_baseline_metrics, write_baseline_metrics_artifact
from schemas.scenario import load_scenario_file
from simulation.kernel import run_turn_based_simulation


def _phase2_result():
    scenario = load_scenario_file("scenarios/baselines/phase2_rule_baseline.json")
    graph = build_graph_from_scenario(scenario)
    return run_turn_based_simulation(
        graph,
        seed=20260329,
        horizon=8,
        scenario_id=scenario.metadata.scenario_id,
    )


def test_compute_baseline_metrics_core_fields() -> None:
    result = _phase2_result()

    payload = compute_baseline_metrics(result)
    assert payload["run_id"] == result.metadata.run_id
    assert payload["timesteps_count"] == 8
    assert "sequence_hash" in payload
    assert "security_outcomes" in payload
    assert "policy_performance" in payload


def test_write_baseline_metrics_artifact_outputs_json() -> None:
    result = _phase2_result()

    with tempfile.TemporaryDirectory() as temp_dir:
        output_path = Path(write_baseline_metrics_artifact(result, temp_dir))
        assert output_path.exists()

        payload = json.loads(output_path.read_text(encoding="utf-8"))
        assert payload["run_id"] == result.metadata.run_id
        assert payload["policy_performance"]["red_offensive_actions"] >= 0
        assert payload["policy_performance"]["blue_containment_actions"] >= 0