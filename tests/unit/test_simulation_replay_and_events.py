from dataclasses import asdict
import json
from pathlib import Path
import tempfile

from environment.graph_builder import build_graph_from_scenario
from schemas.scenario import validate_scenario_dict
from simulation.event_schema import build_timestep_event, validate_event_envelope
from simulation.kernel import run_turn_based_simulation
from simulation.log_writer import write_run_artifacts
from simulation.replay import replay_from_initial_snapshot
from simulation.state_diff import snapshot_payload, snapshot_ref


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


def test_event_envelope_contains_required_provenance() -> None:
    scenario = validate_scenario_dict(_scenario_dict())
    graph = build_graph_from_scenario(scenario)
    result = run_turn_based_simulation(
        graph,
        seed=42,
        horizon=1,
        scenario_id=scenario.metadata.scenario_id,
        scenario_version=scenario.metadata.version,
    )

    event_payload = asdict(build_timestep_event(result.metadata, result.timesteps[0]))
    validate_event_envelope(event_payload)

    assert event_payload["provenance"]["config_hash"]
    assert event_payload["payload"]["post_state_ref"]


def test_replay_matches_final_state_ref() -> None:
    scenario = validate_scenario_dict(_scenario_dict())
    graph = build_graph_from_scenario(scenario)
    result = run_turn_based_simulation(
        graph,
        seed=42,
        horizon=3,
        scenario_id=scenario.metadata.scenario_id,
        scenario_version=scenario.metadata.version,
    )

    replay_frames = replay_from_initial_snapshot(
        snapshot_payload(result.initial_graph),
        [asdict(entry) for entry in result.timesteps],
    )

    assert replay_frames[-1].state_ref == snapshot_ref(result.final_graph)


def test_artifact_writer_outputs_replay_files() -> None:
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
        assert Path(paths["initial_state_file"]).exists()
        assert Path(paths["final_state_file"]).exists()
        assert Path(paths["events_file"]).exists()

        lines = Path(paths["events_file"]).read_text(encoding="utf-8").strip().splitlines()
        payload = json.loads(lines[0])
        validate_event_envelope(payload)
