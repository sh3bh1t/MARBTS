from agents.adaptive import AdaptivePlanningPolicy
from agents.adaptive.ablation import apply_observability_filter
from agents.adaptive.openai_policy import OpenAIAdaptivePolicy
from environment.graph_builder import build_graph_from_scenario
from environment.legal_actions import get_legal_actions
from hart.enums import ActorType
from hart.models import AdaptivePolicyConfig, PolicyContext
from schemas.scenario import validate_scenario_dict
from simulation.state_diff import snapshot_payload


class _FakeParsedResponse:
    def __init__(self, output_parsed) -> None:
        self.output_parsed = output_parsed


class _FakeResponsesClient:
    def __init__(self, output_parsed) -> None:
        self._output_parsed = output_parsed
        self.responses = self

    def parse(self, **_kwargs):
        return _FakeParsedResponse(self._output_parsed)


def _scenario_dict() -> dict:
    return {
        "metadata": {"scenario_id": "adaptive-small", "version": "1.0.0"},
        "nodes": [
            {
                "node_id": "srv-1",
                "node_type": "server",
                "services": ["ssh"],
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


def test_adaptive_policy_selects_legal_action_deterministically() -> None:
    scenario = validate_scenario_dict(_scenario_dict())
    graph = build_graph_from_scenario(scenario)
    legal_actions = get_legal_actions(graph, ActorType.BLUE)
    context = PolicyContext(
        actor=ActorType.BLUE,
        timestep=0,
        scenario_id=scenario.metadata.scenario_id,
        seed=7,
        compromised_nodes=0,
        policy_metrics={},
        state_snapshot=snapshot_payload(graph),
    )

    policy = AdaptivePlanningPolicy(ActorType.BLUE, AdaptivePolicyConfig(planning_depth=3))
    first = policy.select_action(context, legal_actions)
    second = AdaptivePlanningPolicy(ActorType.BLUE, AdaptivePolicyConfig(planning_depth=3)).select_action(context, legal_actions)

    assert first.action in legal_actions
    assert first.action == second.action
    assert first.rationale.trace["planning_depth"] == 3
    assert first.rationale.trace["candidate_values"]


def test_openai_adaptive_policy_accepts_valid_structured_decision() -> None:
    scenario = validate_scenario_dict(_scenario_dict())
    graph = build_graph_from_scenario(scenario)
    legal_actions = get_legal_actions(graph, ActorType.BLUE)
    context = PolicyContext(
        actor=ActorType.BLUE,
        timestep=0,
        scenario_id=scenario.metadata.scenario_id,
        seed=7,
        compromised_nodes=0,
        policy_metrics={},
        state_snapshot=snapshot_payload(graph),
    )
    fake_response = type(
        "DecisionPayload",
        (),
        {
            "action_type": "monitor",
            "targets": ["db-1"],
            "summary": "Monitor the database first.",
            "predicted_effect": "Increase visibility on the high-value asset.",
            "confidence": 0.72,
            "utility_estimate": 6.5,
        },
    )()
    policy = OpenAIAdaptivePolicy(
        ActorType.BLUE,
        AdaptivePolicyConfig(backend="openai", model_name="gpt-5-mini"),
        client=_FakeResponsesClient(fake_response),
    )

    decision = policy.select_action(context, legal_actions)

    assert decision.action.action_type.value == "monitor"
    assert decision.action.targets == ("db-1",)
    assert decision.rationale.trace["backend"] == "openai_responses"
    assert decision.rationale.trace["model_name"] == "gpt-5-mini"


def test_openai_adaptive_policy_falls_back_on_illegal_model_action() -> None:
    scenario = validate_scenario_dict(_scenario_dict())
    graph = build_graph_from_scenario(scenario)
    legal_actions = get_legal_actions(graph, ActorType.BLUE)
    context = PolicyContext(
        actor=ActorType.BLUE,
        timestep=0,
        scenario_id=scenario.metadata.scenario_id,
        seed=7,
        compromised_nodes=0,
        policy_metrics={},
        state_snapshot=snapshot_payload(graph),
    )
    fake_response = type(
        "DecisionPayload",
        (),
        {
            "action_type": "exploit",
            "targets": ["srv-1"],
            "summary": "Illegal choice.",
            "predicted_effect": "Should not be allowed.",
            "confidence": 0.9,
            "utility_estimate": 10.0,
        },
    )()
    policy = OpenAIAdaptivePolicy(
        ActorType.BLUE,
        AdaptivePolicyConfig(backend="openai", fallback_backend="planning"),
        client=_FakeResponsesClient(fake_response),
    )

    decision = policy.select_action(context, legal_actions)

    assert decision.action in legal_actions
    assert "openai_fallback_reason" in decision.rationale.trace


def test_observability_filter_masks_undetected_details() -> None:
    scenario = validate_scenario_dict(_scenario_dict())
    graph = build_graph_from_scenario(scenario)
    filtered = apply_observability_filter(
        snapshot_payload(graph),
        AdaptivePolicyConfig(feature_flags={"reduced_observability": True}),
    )

    assert filtered["nodes"]["srv-1"]["services"] == []
    assert filtered["nodes"]["srv-1"]["vulnerabilities"] == []
    assert filtered["nodes"]["srv-1"]["compromised_state"] == "none"


def test_no_planning_ablation_is_reflected_in_trace() -> None:
    scenario = validate_scenario_dict(_scenario_dict())
    graph = build_graph_from_scenario(scenario)
    legal_actions = get_legal_actions(graph, ActorType.BLUE)
    context = PolicyContext(
        actor=ActorType.BLUE,
        timestep=0,
        scenario_id=scenario.metadata.scenario_id,
        seed=7,
        compromised_nodes=0,
        policy_metrics={},
        state_snapshot=snapshot_payload(graph),
    )

    policy = AdaptivePlanningPolicy(
        ActorType.BLUE,
        AdaptivePolicyConfig(planning_depth=3, feature_flags={"no_planning": True}),
    )
    decision = policy.select_action(context, legal_actions)

    assert decision.action in legal_actions
    assert decision.rationale.trace["planning_depth"] == 0
    assert "no_planning=True" in decision.rationale.trace["notes"]
