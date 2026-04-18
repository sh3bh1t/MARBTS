from pathlib import Path
import tempfile

from environment.graph_builder import build_graph_from_scenario
from schemas.scenario import validate_scenario_dict
from simulation.artifact_loader import load_run_artifacts, reconstruct_run_replay, validate_run_artifacts
from simulation.kernel import run_turn_based_simulation
from simulation.log_writer import write_run_artifacts
from simulation.state_diff import snapshot_ref


def _scenario_dict() -> dict:
    return {
        "metadata": {"scenario_id": "phase4-small", "version": "1.0.0"},
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


def test_load_and_validate_run_artifacts_and_replay() -> None:
    scenario = validate_scenario_dict(_scenario_dict())
    graph = build_graph_from_scenario(scenario)
    result = run_turn_based_simulation(
        graph,
        seed=42,
        horizon=3,
        scenario_id=scenario.metadata.scenario_id,
        scenario_version=scenario.metadata.version,
    )

    with tempfile.TemporaryDirectory() as temp_dir:
        paths = write_run_artifacts(result, temp_dir)
        run_artifacts = load_run_artifacts(Path(paths["run_dir"]))
        validation = validate_run_artifacts(run_artifacts)
        replay_frames = reconstruct_run_replay(run_artifacts)

        assert validation["log_completeness_ratio"] == 1.0
        assert validation["timeline_rows"]
        assert validation["action_type_counts"]["red"]
        assert replay_frames[-1]["state_ref"] == snapshot_ref(result.final_graph)
