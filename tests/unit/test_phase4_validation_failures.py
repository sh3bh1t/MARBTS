import json
from pathlib import Path
import tempfile

from environment.graph_builder import build_graph_from_scenario
from schemas.scenario import validate_scenario_dict
from simulation.artifact_loader import load_run_artifacts, validate_run_artifacts
from simulation.kernel import run_turn_based_simulation
from simulation.log_writer import write_run_artifacts


def _scenario_dict() -> dict:
    return {
        "metadata": {"scenario_id": "phase4-failure", "version": "1.0.0"},
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


def test_validate_run_artifacts_fails_on_event_payload_mismatch() -> None:
    scenario = validate_scenario_dict(_scenario_dict())
    graph = build_graph_from_scenario(scenario)
    result = run_turn_based_simulation(
        graph,
        seed=42,
        horizon=2,
        scenario_id=scenario.metadata.scenario_id,
        scenario_version=scenario.metadata.version,
    )

    with tempfile.TemporaryDirectory() as temp_dir:
        paths = write_run_artifacts(result, temp_dir)
        events_path = Path(paths["events_file"])
        lines = events_path.read_text(encoding="utf-8").splitlines()
        payload = json.loads(lines[0])
        payload["payload"]["pre_state_ref"] = "broken-ref"
        lines[0] = json.dumps(payload, sort_keys=True)
        events_path.write_text("\n".join(lines) + "\n", encoding="utf-8")

        loaded = load_run_artifacts(paths["run_dir"])
        try:
            validate_run_artifacts(loaded)
        except ValueError as exc:
            assert "event/timestep consistency failures" in str(exc)
        else:
            raise AssertionError("validate_run_artifacts should fail on mismatched event payload")
