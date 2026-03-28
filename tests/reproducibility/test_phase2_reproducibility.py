from __future__ import annotations

from environment.graph_builder import build_graph_from_scenario
from schemas.scenario import load_scenario_file
from simulation.kernel import run_turn_based_simulation
from simulation.policy_trace import action_sequence_hash


def test_phase2_same_seed_produces_same_action_sequence_hash() -> None:
    scenario = load_scenario_file("scenarios/baselines/phase2_rule_baseline.json")
    graph = build_graph_from_scenario(scenario)

    first = run_turn_based_simulation(
        graph,
        seed=20260329,
        horizon=8,
        scenario_id=scenario.metadata.scenario_id,
    )
    second = run_turn_based_simulation(
        graph,
        seed=20260329,
        horizon=8,
        scenario_id=scenario.metadata.scenario_id,
    )

    assert action_sequence_hash(first) == action_sequence_hash(second)