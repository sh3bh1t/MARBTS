from environment.graph_builder import build_graph_from_scenario
from schemas.scenario import validate_scenario_dict
from simulation.kernel import run_turn_based_simulation


def _scenario_dict() -> dict:
    return {
        "metadata": {"scenario_id": "kernel-small", "version": "1.0.0"},
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


def _deterministic_selector(actor, legal_actions, _rng, _timestep):
    ranked = sorted(legal_actions, key=lambda action: (action.action_type, action.targets))

    if actor == "red":
        for action in ranked:
            if action.action_type == "exploit" and action.targets == ("srv-1",):
                return action

    if actor == "blue":
        for action in ranked:
            if action.action_type == "monitor":
                return action

    return ranked[0]


def test_single_step_state_transition() -> None:
    scenario = validate_scenario_dict(_scenario_dict())
    graph = build_graph_from_scenario(scenario)

    result = run_turn_based_simulation(
        graph,
        seed=7,
        horizon=1,
        scenario_id="kernel-small",
        selector=_deterministic_selector,
    )

    assert len(result.timesteps) == 1
    assert result.final_graph.nodes["srv-1"]["compromised_state"] == "user"


def test_logging_completeness_fields_present() -> None:
    scenario = validate_scenario_dict(_scenario_dict())
    graph = build_graph_from_scenario(scenario)

    result = run_turn_based_simulation(
        graph,
        seed=11,
        horizon=2,
        scenario_id="kernel-small",
        selector=_deterministic_selector,
    )

    entry = result.timesteps[0]
    assert entry.pre_state_ref
    assert entry.red_action_intent.rationale
    assert entry.blue_action_intent.rationale
    assert "changed_nodes" in entry.post_state_diff
    assert "compromised_nodes_delta" in entry.metric_delta


def test_seed_reproducibility() -> None:
    scenario = validate_scenario_dict(_scenario_dict())
    graph = build_graph_from_scenario(scenario)

    first = run_turn_based_simulation(
        graph,
        seed=123,
        horizon=3,
        scenario_id="kernel-small",
    )
    second = run_turn_based_simulation(
        graph,
        seed=123,
        horizon=3,
        scenario_id="kernel-small",
    )

    first_trace = [
        (
            entry.red_action_intent.action_type,
            entry.red_action_intent.targets,
            entry.blue_action_intent.action_type,
            entry.blue_action_intent.targets,
            entry.metric_delta["compromised_nodes_after"],
        )
        for entry in first.timesteps
    ]
    second_trace = [
        (
            entry.red_action_intent.action_type,
            entry.red_action_intent.targets,
            entry.blue_action_intent.action_type,
            entry.blue_action_intent.targets,
            entry.metric_delta["compromised_nodes_after"],
        )
        for entry in second.timesteps
    ]

    assert first_trace == second_trace
