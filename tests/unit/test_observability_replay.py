from __future__ import annotations

from pathlib import Path
import tempfile

from environment.graph_builder import build_graph_from_scenario
from schemas.scenario import validate_scenario_dict
from simulation.kernel import run_turn_based_simulation
from simulation.log_writer import write_run_artifacts

from observability.replay import load_run_artifact_bundle


def _scenario_dict() -> dict:
    return {
        "metadata": {"scenario_id": "replay-small", "version": "1.0.0"},
        "nodes": [
            {
                "node_id": "srv-1",
                "node_type": "server",
                "services": ["ssh", "http"],
                "vulnerabilities": ["cve-sim-001"],
                "security_level": 3,
                "compromised_state": "none",
                "detection_state": "undetected",
                "isolation_state": False,
            },
            {
                "node_id": "db-1",
                "node_type": "database",
                "services": ["postgres"],
                "vulnerabilities": ["cve-sim-010"],
                "security_level": 4,
                "compromised_state": "none",
                "detection_state": "undetected",
                "isolation_state": False,
            },
        ],
        "edges": [{"source": "srv-1", "target": "db-1"}],
    }


def test_load_run_artifact_bundle_reconstructs_replay_summary() -> None:
    scenario = validate_scenario_dict(_scenario_dict())
    graph = build_graph_from_scenario(scenario)
    result = run_turn_based_simulation(graph, seed=42, horizon=3, scenario_id="replay-small")

    with tempfile.TemporaryDirectory() as temp_dir:
        paths = write_run_artifacts(result, temp_dir)
        bundle = load_run_artifact_bundle(paths["run_dir"])

        assert bundle["summary"]["run_id"] == result.metadata.run_id
        assert bundle["summary"]["scenario_id"] == "replay-small"
        assert bundle["summary"]["timesteps_count"] == 3
        assert bundle["summary"]["sequence_hash_matches"] is True
        assert bundle["summary"]["sequence_hash"] == bundle["summary"]["replay_sequence_hash"]
        assert bundle["summary"]["final_compromised_nodes"] >= 0
        assert bundle["frames"]
