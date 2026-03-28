import pytest

from schemas.scenario import load_scenario_file, validate_scenario_dict


def _valid_scenario_dict() -> dict:
    return {
        "metadata": {"scenario_id": "baseline-small", "version": "1.0.0"},
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


def test_validate_valid_scenario() -> None:
    scenario = validate_scenario_dict(_valid_scenario_dict())
    assert scenario.metadata.scenario_id == "baseline-small"
    assert len(scenario.nodes) == 2
    assert len(scenario.edges) == 1


def test_reject_missing_required_node_field() -> None:
    payload = _valid_scenario_dict()
    del payload["nodes"][0]["security_level"]

    with pytest.raises(ValueError, match="missing required fields"):
        validate_scenario_dict(payload)


def test_reject_edge_with_unknown_node_reference() -> None:
    payload = _valid_scenario_dict()
    payload["edges"] = [{"source": "srv-1", "target": "ghost-node"}]

    with pytest.raises(ValueError, match="references undefined node_id"):
        validate_scenario_dict(payload)


def test_load_valid_baseline_file() -> None:
    scenario = load_scenario_file("scenarios/baselines/minimal_valid.json")
    assert scenario.metadata.version == "1.0.0"
