import json
from pathlib import Path
import tempfile

from environment.graph_builder import build_graph_from_scenario
from schemas.scenario import validate_scenario_dict
from simulation.kernel import run_turn_based_simulation
from simulation.log_writer import write_run_artifacts
from simulation.state_diff import snapshot_payload, snapshot_ref


def _scenario_dict() -> dict:
    return {
        "metadata": {"scenario_id": "artifacts-small", "version": "1.0.0"},
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


def test_snapshot_ref_is_deterministic() -> None:
    scenario = validate_scenario_dict(_scenario_dict())
    graph = build_graph_from_scenario(scenario)

    first = snapshot_ref(graph)
    second = snapshot_ref(graph)
    assert first == second


def test_post_state_diff_fields_available() -> None:
    scenario = validate_scenario_dict(_scenario_dict())
    graph = build_graph_from_scenario(scenario)

    payload = snapshot_payload(graph)
    payload_mutated = json.loads(json.dumps(payload))
    payload_mutated["nodes"]["srv-1"]["compromised_state"] = "user"

    from simulation.state_diff import compute_post_state_diff

    diff = compute_post_state_diff(payload, payload_mutated)
    assert "changed_nodes" in diff
    assert "removed_edges" in diff
    assert "added_edges" in diff
    assert diff["changed_nodes"][0]["node_id"] == "srv-1"


def test_run_artifacts_writer_outputs_metadata_and_jsonl() -> None:
    scenario = validate_scenario_dict(_scenario_dict())
    graph = build_graph_from_scenario(scenario)

    result = run_turn_based_simulation(
        graph,
        seed=42,
        horizon=2,
        scenario_id="artifacts-small",
    )

    with tempfile.TemporaryDirectory() as temp_dir:
        paths = write_run_artifacts(result, temp_dir)
        metadata_path = Path(paths["metadata_file"])
        timesteps_path = Path(paths["timesteps_file"])
        policy_metrics_path = Path(paths["policy_metrics_file"])

        assert metadata_path.exists()
        assert timesteps_path.exists()
        assert policy_metrics_path.exists()

        metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
        assert metadata["seed"] == 42
        assert metadata["scenario_id"] == "artifacts-small"
        assert metadata["timesteps_count"] == 2
        assert "final_state_ref" in metadata
        assert metadata["schema_version"] == "2026-04-23.observability.v1"
        assert metadata["event_type"] == "run_metadata"
        assert metadata["provenance"]["commit_hash"]
        assert metadata["provenance"]["config_hash"]

        lines = timesteps_path.read_text(encoding="utf-8").strip().splitlines()
        assert len(lines) == 2
        first_line = json.loads(lines[0])
        assert first_line["schema_version"] == "2026-04-23.observability.v1"
        assert first_line["event_type"] == "timestep"
        assert first_line["provenance"]["run_id"] == metadata["run_id"]
        assert "pre_state_ref" in first_line
        assert "post_state_ref" in first_line
        assert "red_action_intent" in first_line
        assert "blue_action_intent" in first_line
        assert "post_state_diff" in first_line
        assert "metric_delta" in first_line

        policy_metrics = json.loads(policy_metrics_path.read_text(encoding="utf-8"))
        assert "sequence_hash" in policy_metrics
        assert "action_counts" in policy_metrics
        assert "policy_metrics" in policy_metrics
        assert policy_metrics["schema_version"] == "2026-04-23.observability.v1"
        assert policy_metrics["event_type"] == "policy_metrics"
        assert policy_metrics["provenance"]["scenario_id"] == "artifacts-small"
