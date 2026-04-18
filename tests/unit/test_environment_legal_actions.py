import pytest

from environment.graph_builder import build_graph_from_scenario
from environment.legal_actions import get_legal_actions
from schemas.scenario import validate_scenario_dict


def _scenario_dict() -> dict:
    return {
        "metadata": {"scenario_id": "legal-actions-small", "version": "1.0.0"},
        "nodes": [
            {
                "node_id": "srv-1",
                "node_type": "server",
                "services": ["ssh", "http"],
                "vulnerabilities": ["cve-sim-001"],
                "security_level": 3,
                "compromised_state": "user",
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
            {
                "node_id": "iot-1",
                "node_type": "iot",
                "services": ["mqtt"],
                "vulnerabilities": [],
                "security_level": 9,
                "compromised_state": "none",
                "detection_state": "undetected",
                "isolation_state": True,
            },
        ],
        "edges": [
            {"source": "srv-1", "target": "db-1"},
            {"source": "db-1", "target": "iot-1"},
        ],
    }


@pytest.fixture
def graph():
    scenario = validate_scenario_dict(_scenario_dict())
    return build_graph_from_scenario(scenario)


def test_red_actions_include_scan_exploit_escalate_lateral(graph) -> None:
    actions = get_legal_actions(graph, "red")
    tuples = {(action.action_type, action.targets) for action in actions}

    assert ("scan", ("srv-1",)) in tuples
    assert ("exploit", ("srv-1",)) in tuples
    assert ("escalate", ("srv-1",)) in tuples
    assert ("lateral_move", ("srv-1", "db-1")) in tuples


def test_red_actions_skip_isolated_targets(graph) -> None:
    actions = get_legal_actions(graph, "red")
    isolated_actions = [action for action in actions if "iot-1" in action.targets and action.action_type != "lateral_move"]

    assert isolated_actions == []


def test_blue_actions_include_monitor_patch_isolate_block_and_decoy(graph) -> None:
    actions = get_legal_actions(graph, "blue")
    tuples = {(action.action_type, action.targets) for action in actions}

    assert ("monitor", ("srv-1",)) in tuples
    assert ("patch", ("srv-1",)) in tuples
    assert ("isolate", ("srv-1",)) in tuples
    assert ("decoy", ("srv-1",)) in tuples
    assert ("feint", ("srv-1",)) in tuples
    assert ("block", ("db-1", "iot-1")) in tuples


def test_legal_actions_are_deterministic(graph) -> None:
    first = get_legal_actions(graph, "blue")
    second = get_legal_actions(graph, "blue")
    assert first == second


def test_invalid_actor_rejected(graph) -> None:
    with pytest.raises(ValueError, match="unsupported actor"):
        get_legal_actions(graph, "purple")
