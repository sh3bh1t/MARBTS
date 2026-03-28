from environment.graph_builder import build_graph_from_scenario
from environment.state import initialize_simulation_state
from schemas.scenario import validate_scenario_dict


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


def test_build_graph_from_scenario() -> None:
    scenario = validate_scenario_dict(_valid_scenario_dict())
    graph = build_graph_from_scenario(scenario)

    assert graph.number_of_nodes() == 2
    assert graph.number_of_edges() == 1
    assert graph.has_edge("srv-1", "db-1")

    srv_attrs = graph.nodes["srv-1"]
    assert srv_attrs["node_type"] == "server"
    assert srv_attrs["security_level"] == 3
    assert srv_attrs["compromised_state"] == "none"


def test_initialize_simulation_state() -> None:
    scenario = validate_scenario_dict(_valid_scenario_dict())
    state = initialize_simulation_state(scenario)

    assert state.scenario_id == "baseline-small"
    assert state.timestep == 0
    assert "srv-1" in state.nodes
    assert state.nodes["srv-1"].security_level == 3
    assert state.nodes["srv-1"].detection_state == "undetected"
