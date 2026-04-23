from __future__ import annotations

from agents.adaptive import AdaptivePlanningPolicy
from agents.interfaces.policy import PolicyRegistry
from environment.graph_builder import build_graph_from_scenario
from environment.legal_actions import get_legal_actions
from hart.enums import ActionType, ActorType
from hart.models import AdaptivePolicyConfig, LegalAction, PolicyContext
from schemas.scenario import validate_scenario_dict
from simulation.kernel import run_turn_based_simulation


def _scenario_dict() -> dict:
    return {
        "metadata": {"scenario_id": "phase3-adaptive-small", "version": "1.0.0"},
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


def test_adaptive_red_policy_is_deterministic_for_same_input() -> None:
    graph = _build_graph()
    legal_actions = get_legal_actions(graph, ActorType.RED)
    context = PolicyContext(
        actor=ActorType.RED,
        timestep=0,
        scenario_id="phase3-adaptive-small",
        seed=42,
        compromised_nodes=1,
        policy_metrics={},
    )

    policy = AdaptivePlanningPolicy(
        actor=ActorType.RED,
        config=AdaptivePolicyConfig(planning_horizon=3, discount_factor=0.9, exploration_bias=0.0),
    )

    first = policy.select_action(context, legal_actions)
    second = policy.select_action(context, legal_actions)

    assert first.action == second.action
    assert first.rationale.tie_breaker == "(-score, action_type, targets)"
    assert first.rationale.planning_trace is not None
    assert first.rationale.inference_record is not None


def test_adaptive_policy_rejects_unsafe_action_set() -> None:
    policy = AdaptivePlanningPolicy(actor=ActorType.RED)
    illegal_actions = (
        LegalAction(
            actor=ActorType.BLUE,
            action_type=ActionType.MONITOR,
            targets=("srv-1",),
            rationale_hint="not valid for red policy",
        ),
    )
    context = PolicyContext(
        actor=ActorType.RED,
        timestep=1,
        scenario_id="phase3-adaptive-small",
        seed=99,
        compromised_nodes=1,
        policy_metrics={},
    )

    try:
        policy.select_action(context, illegal_actions)
    except ValueError as exc:
        assert str(exc) == "no safe legal actions available for adaptive policy"
    else:
        raise AssertionError("expected ValueError for unsafe legal action set")


def test_kernel_with_adaptive_policies_emits_planning_payloads() -> None:
    graph = _build_graph()
    config = AdaptivePolicyConfig(planning_horizon=3, discount_factor=0.9, exploration_bias=0.0)

    registry = PolicyRegistry()
    registry.register(AdaptivePlanningPolicy(actor=ActorType.RED, config=config))
    registry.register(AdaptivePlanningPolicy(actor=ActorType.BLUE, config=config))

    result = run_turn_based_simulation(
        graph,
        seed=20260423,
        horizon=2,
        scenario_id="phase3-adaptive-small",
        policy_registry=registry,
    )

    assert len(result.timesteps) == 2

    for timestep in result.timesteps:
        red_payload = timestep.red_action_intent.rationale_payload
        blue_payload = timestep.blue_action_intent.rationale_payload

        assert red_payload["policy_name"].startswith("adaptive_planning_red")
        assert blue_payload["policy_name"].startswith("adaptive_planning_blue")
        assert red_payload["planning_trace"]["horizon"] == 3
        assert blue_payload["planning_trace"]["horizon"] == 3
        assert red_payload["inference_record"]["deterministic"] is True
        assert blue_payload["inference_record"]["deterministic"] is True


def test_adaptive_reduced_observability_flag_is_reflected_in_rationale_payload() -> None:
    graph = _build_graph()
    legal_actions = get_legal_actions(graph, ActorType.RED)
    context = PolicyContext(
        actor=ActorType.RED,
        timestep=2,
        scenario_id="phase3-adaptive-small",
        seed=7,
        compromised_nodes=5,
        policy_metrics={},
    )

    policy = AdaptivePlanningPolicy(
        actor=ActorType.RED,
        config=AdaptivePolicyConfig(
            planning_horizon=3,
            discount_factor=0.9,
            exploration_bias=0.0,
            reduced_observability=True,
        ),
    )

    decision = policy.select_action(context, legal_actions)

    assert decision.rationale.score_breakdown.components["reduced_observability"] == 1.0
    assert decision.rationale.inference_record is not None
    assert decision.rationale.inference_record.input_features["reduced_observability"] is True


def test_adaptive_deception_hooks_are_disabled_by_default() -> None:
    graph = _build_graph()
    legal_actions = get_legal_actions(graph, ActorType.BLUE)
    context = PolicyContext(
        actor=ActorType.BLUE,
        timestep=3,
        scenario_id="phase3-adaptive-small",
        seed=11,
        compromised_nodes=2,
        policy_metrics={},
    )

    policy = AdaptivePlanningPolicy(actor=ActorType.BLUE, config=AdaptivePolicyConfig(exploration_bias=0.0))
    decision = policy.select_action(context, legal_actions)

    assert decision.rationale.deception_event is None
    assert decision.rationale.score_breakdown.components["deception_triggered"] == 0.0
    assert decision.rationale.score_breakdown.components["deception_bonus"] == 0.0


def test_adaptive_deception_hooks_emit_deception_event_when_enabled() -> None:
    graph = _build_graph()
    legal_actions = get_legal_actions(graph, ActorType.BLUE)
    context = PolicyContext(
        actor=ActorType.BLUE,
        timestep=4,
        scenario_id="phase3-adaptive-small",
        seed=12,
        compromised_nodes=4,
        policy_metrics={},
    )

    policy = AdaptivePlanningPolicy(
        actor=ActorType.BLUE,
        config=AdaptivePolicyConfig(
            planning_horizon=3,
            discount_factor=0.9,
            exploration_bias=0.0,
            enable_decoy=True,
            enable_bluff=True,
            deception_bias=1.0,
        ),
    )
    decision = policy.select_action(context, legal_actions)

    assert decision.rationale.deception_event is not None
    assert decision.rationale.deception_event.tactic in {"decoy", "bluff"}
    assert decision.rationale.score_breakdown.components["deception_triggered"] == 1.0
    assert decision.rationale.score_breakdown.components["deception_bonus"] > 0.0
    assert decision.rationale.inference_record is not None
    assert decision.rationale.inference_record.input_features["deception_tactic"] == decision.rationale.deception_event.tactic


def test_adaptive_policy_defaults_to_heuristic_routing_without_model_config() -> None:
    graph = _build_graph()
    legal_actions = get_legal_actions(graph, ActorType.BLUE)
    context = PolicyContext(
        actor=ActorType.BLUE,
        timestep=5,
        scenario_id="phase3-adaptive-small",
        seed=13,
        compromised_nodes=3,
        policy_metrics={},
    )

    policy = AdaptivePlanningPolicy(actor=ActorType.BLUE, config=AdaptivePolicyConfig(exploration_bias=0.0))
    decision = policy.select_action(context, legal_actions)

    assert decision.rationale.inference_record is not None
    assert decision.rationale.inference_record.model_family == "heuristic_planner"
    assert decision.rationale.inference_record.deterministic is True
    assert decision.rationale.score_breakdown.components["deception_triggered"] == 0.0
