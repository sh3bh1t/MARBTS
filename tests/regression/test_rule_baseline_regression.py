from __future__ import annotations

from environment.graph_builder import build_graph_from_scenario
from schemas.scenario import load_scenario_file
from simulation.kernel import run_turn_based_simulation
from simulation.policy_trace import action_sequence_hash


def test_rule_baseline_action_sequence_regression_signature() -> None:
    scenario = load_scenario_file("scenarios/baselines/rule_baseline.json")
    graph = build_graph_from_scenario(scenario)

    result = run_turn_based_simulation(
        graph,
        seed=20260329,
        horizon=8,
        scenario_id=scenario.metadata.scenario_id,
    )

    assert action_sequence_hash(result) == "7012ba553c213ecb022817158aff42542c4cb423ad2f447fb092d395b0b68219"