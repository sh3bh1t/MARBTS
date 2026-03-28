import pytest

from environment.graph_builder import build_graph_from_scenario
from environment.transitions import apply_block, apply_exploit, apply_isolate, apply_patch
from schemas.scenario import validate_scenario_dict


def _scenario_dict() -> dict:
    return {
        "metadata": {"scenario_id": "transitions-small", "version": "1.0.0"},
        "nodes": [
            {
                "node_id": "srv-1",
                "node_type": "server",
                "services": ["ssh", "http"],
                "vulnerabilities": ["cve-sim-001", "cve-sim-002"],
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


@pytest.fixture
def graph():
    scenario = validate_scenario_dict(_scenario_dict())
    return build_graph_from_scenario(scenario)


def test_exploit_progression_and_cap(graph) -> None:
    graph_1, result_1 = apply_exploit(graph, "srv-1")
    assert result_1.changed
    assert graph_1.nodes["srv-1"]["compromised_state"] == "user"

    graph_2, result_2 = apply_exploit(graph_1, "srv-1")
    assert result_2.changed
    assert graph_2.nodes["srv-1"]["compromised_state"] == "privileged"

    graph_3, result_3 = apply_exploit(graph_2, "srv-1")
    assert not result_3.changed
    assert graph_3.nodes["srv-1"]["compromised_state"] == "privileged"


def test_patch_reduces_compromise_and_hardens(graph) -> None:
    graph_1, _ = apply_exploit(graph, "srv-1")
    graph_2, result = apply_patch(graph_1, "srv-1")

    assert result.changed
    assert graph_2.nodes["srv-1"]["compromised_state"] == "none"
    assert graph_2.nodes["srv-1"]["security_level"] == 4
    assert graph_2.nodes["srv-1"]["vulnerabilities"] == ["cve-sim-002"]


def test_isolate_sets_flag_and_removes_edges(graph) -> None:
    assert graph.has_edge("srv-1", "db-1")

    isolated_graph, result = apply_isolate(graph, "srv-1")

    assert result.changed
    assert isolated_graph.nodes["srv-1"]["isolation_state"]
    assert not isolated_graph.has_edge("srv-1", "db-1")


def test_block_removes_edge(graph) -> None:
    blocked_graph, result = apply_block(graph, "srv-1", "db-1")

    assert result.changed
    assert not blocked_graph.has_edge("srv-1", "db-1")


def test_unknown_node_rejected(graph) -> None:
    with pytest.raises(ValueError, match="unknown node"):
        apply_patch(graph, "ghost-node")
