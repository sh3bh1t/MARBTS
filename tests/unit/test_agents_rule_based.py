from __future__ import annotations

from agents.blue.rule_based import RuleBasedBluePolicy
from agents.red.rule_based import RuleBasedRedPolicy
from environment.graph_builder import build_graph_from_scenario
from environment.legal_actions import get_legal_actions
from hart.enums import ActionType, ActorType
from hart.models import LegalAction, PolicyContext
from schemas.scenario import validate_scenario_dict
from simulation.kernel import run_turn_based_simulation


def _scenario_dict() -> dict:
    return {
        "metadata": {"scenario_id": "phase2-policy-small", "version": "1.0.0"},
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
        ],
        "edges": [{"source": "srv-1", "target": "db-1"}],
    }


def _build_graph():
    scenario = validate_scenario_dict(_scenario_dict())
    return build_graph_from_scenario(scenario)


def test_red_policy_is_deterministic_for_same_input() -> None:
    graph = _build_graph()
    policy = RuleBasedRedPolicy()
    legal_actions = get_legal_actions(graph, "red")
    context = PolicyContext(
        actor=ActorType.RED,
        timestep=0,
        scenario_id="phase2-policy-small",
        seed=42,
        compromised_nodes=1,
        policy_metrics={},
    )

    first = policy.select_action(context, legal_actions)
    second = policy.select_action(context, legal_actions)

    assert first.action == second.action
    assert first.rationale.tie_breaker == "(-score, action_type, targets)"


def test_blue_policy_prioritizes_containment_under_threat() -> None:
    graph = _build_graph()
    policy = RuleBasedBluePolicy()
    legal_actions = get_legal_actions(graph, "blue")
    context = PolicyContext(
        actor=ActorType.BLUE,
        timestep=0,
        scenario_id="phase2-policy-small",
        seed=42,
        compromised_nodes=2,
        policy_metrics={},
    )

    decision = policy.select_action(context, legal_actions)
    assert decision.action.action_type in {ActionType.BLOCK, ActionType.ISOLATE}


def test_blue_policy_can_select_decoy_over_isolate_when_threat_is_low() -> None:
    policy = RuleBasedBluePolicy()
    legal_actions = (
        LegalAction(actor=ActorType.BLUE, action_type=ActionType.DECOY, targets=("srv-1",), rationale_hint="deploy decoy"),
        LegalAction(actor=ActorType.BLUE, action_type=ActionType.ISOLATE, targets=("srv-1",), rationale_hint="contain node"),
    )
    context = PolicyContext(
        actor=ActorType.BLUE,
        timestep=0,
        scenario_id="blue-decoy",
        seed=42,
        compromised_nodes=0,
        policy_metrics={},
    )

    decision = policy.select_action(context, legal_actions)
    assert decision.action.action_type == ActionType.DECOY


def test_blue_policy_can_select_feint_when_only_deception_options_remain() -> None:
    policy = RuleBasedBluePolicy()
    legal_actions = (
        LegalAction(actor=ActorType.BLUE, action_type=ActionType.FEINT, targets=("srv-1",), rationale_hint="deploy feint"),
        LegalAction(actor=ActorType.BLUE, action_type=ActionType.MONITOR, targets=("srv-1",), rationale_hint="monitor"),
    )
    context = PolicyContext(
        actor=ActorType.BLUE,
        timestep=0,
        scenario_id="blue-feint",
        seed=42,
        compromised_nodes=1,
        policy_metrics={},
    )

    decision = policy.select_action(context, legal_actions)
    assert decision.action.action_type == ActionType.FEINT


def test_tie_breaker_prefers_lexicographic_targets() -> None:
    policy = RuleBasedBluePolicy()
    legal_actions = (
        LegalAction(actor=ActorType.BLUE, action_type=ActionType.MONITOR, targets=("b-node",), rationale_hint="monitor b"),
        LegalAction(actor=ActorType.BLUE, action_type=ActionType.MONITOR, targets=("a-node",), rationale_hint="monitor a"),
    )
    context = PolicyContext(
        actor=ActorType.BLUE,
        timestep=0,
        scenario_id="tie-break",
        seed=123,
        compromised_nodes=0,
        policy_metrics={},
    )

    decision = policy.select_action(context, legal_actions)
    assert decision.action.targets == ("a-node",)


def test_kernel_policy_actions_are_legal_and_explainable() -> None:
    graph = _build_graph()
    result = run_turn_based_simulation(
        graph,
        seed=99,
        horizon=3,
        scenario_id="phase2-policy-small",
    )

    for timestep in result.timesteps:
        assert timestep.red_action_intent.rationale
        assert timestep.blue_action_intent.rationale
        assert "policy_name" in timestep.red_action_intent.rationale_payload
        assert "policy_name" in timestep.blue_action_intent.rationale_payload
        assert "policy_metrics" in timestep.metric_delta
