from __future__ import annotations

from dataclasses import asdict
from datetime import datetime, timezone
import hashlib
from typing import Callable

import networkx as nx

from agents.blue.rule_based import RuleBasedBluePolicy
from agents.interfaces.policy import PolicyDecision, PolicyRegistry
from agents.red.rule_based import RuleBasedRedPolicy
from environment.legal_actions import LegalAction, get_legal_actions
from environment.transitions import TransitionResult, apply_block, apply_exploit, apply_isolate, apply_patch
from hart.enums import ActionType, ActorType
from hart.models import ActionRecord, PolicyContext, PolicyMetricsSnapshot, RunMetadata, SimulationRunResult, TimestepLogEntry
from simulation.rng import SeededRNG
from simulation.state_diff import compute_post_state_diff, snapshot_payload, snapshot_ref


ActionSelector = Callable[[str, tuple[LegalAction, ...], SeededRNG, int], LegalAction]


def _build_default_policy_registry() -> PolicyRegistry:
    registry = PolicyRegistry()
    registry.register(RuleBasedRedPolicy())
    registry.register(RuleBasedBluePolicy())
    return registry


def _count_compromised(graph: nx.Graph) -> int:
    total = 0
    for _, attrs in graph.nodes(data=True):
        if attrs.get("compromised_state") in {"user", "privileged"}:
            total += 1
    return total


def _apply_red_action(graph: nx.Graph, action: LegalAction, rng=None) -> tuple[nx.Graph, TransitionResult]:
    if action.action_type == ActionType.EXPLOIT:
        return apply_exploit(graph, action.targets[0], rng=rng)

    if action.action_type == ActionType.ESCALATE:
        return apply_exploit(graph, action.targets[0], rng=rng)

    if action.action_type == ActionType.LATERAL_MOVE:
        return apply_exploit(graph, action.targets[1], rng=rng)

    return graph, TransitionResult(
        action=action.action_type,
        target=":".join(action.targets),
        changed=False,
        reason="no state mutation for informational action",
    )


def _apply_blue_action(graph: nx.Graph, action: LegalAction) -> tuple[nx.Graph, TransitionResult]:
    if action.action_type == ActionType.PATCH:
        return apply_patch(graph, action.targets[0])

    if action.action_type == ActionType.ISOLATE:
        return apply_isolate(graph, action.targets[0])

    if action.action_type == ActionType.BLOCK:
        return apply_block(graph, action.targets[0], action.targets[1])

    return graph, TransitionResult(
        action=action.action_type,
        target=":".join(action.targets),
        changed=False,
        reason="no state mutation for informational action",
    )


def _default_selector(_actor: str, legal_actions: tuple[LegalAction, ...], rng: SeededRNG, _timestep: int) -> LegalAction:
    return rng.choice(legal_actions)


def _to_action_record(
    actor: str,
    legal_action: LegalAction,
    transition: TransitionResult,
    policy_decision: PolicyDecision | None = None,
) -> ActionRecord:
    rationale = legal_action.rationale_hint
    rationale_payload: dict = {"source": "legal_action_hint"}

    if policy_decision is not None:
        rationale = policy_decision.rationale.summary
        rationale_payload = asdict(policy_decision.rationale)

    return ActionRecord(
        actor=actor,
        action_type=legal_action.action_type.value,
        targets=legal_action.targets,
        rationale=rationale,
        rationale_payload=rationale_payload,
        changed=transition.changed,
        reason=transition.reason,
    )


def _build_policy_context(
    *,
    actor: ActorType,
    timestep: int,
    scenario_id: str,
    seed: int,
    graph: nx.Graph,
    metrics_snapshot: PolicyMetricsSnapshot | None,
) -> PolicyContext:
    policy_metrics = {}
    if metrics_snapshot is not None:
        policy_metrics = dict(metrics_snapshot.action_type_counts)

    return PolicyContext(
        actor=actor,
        timestep=timestep,
        scenario_id=scenario_id,
        seed=seed,
        compromised_nodes=_count_compromised(graph),
        policy_metrics=policy_metrics,
    )


def run_turn_based_simulation(
    initial_graph: nx.Graph,
    *,
    seed: int,
    horizon: int,
    scenario_id: str,
    selector: ActionSelector | None = None,
    policy_registry: PolicyRegistry | None = None,
    exploit_resistance: bool = False,
) -> SimulationRunResult:
    if horizon < 1:
        raise ValueError("horizon must be >= 1")

    policy_selector = selector or _default_selector
    runtime_policy_registry = policy_registry or _build_default_policy_registry()
    rng = SeededRNG(seed)

    current_graph = initial_graph.copy()
    timestep_logs: list[TimestepLogEntry] = []
    turn_graphs: list[nx.Graph] = []

    run_id_input = f"{scenario_id}:{seed}:{horizon}:{snapshot_ref(current_graph)}"
    run_id = hashlib.sha256(run_id_input.encode("utf-8")).hexdigest()[:16]

    red_metrics: PolicyMetricsSnapshot | None = None
    blue_metrics: PolicyMetricsSnapshot | None = None

    for timestep in range(horizon):
        pre_payload = snapshot_payload(current_graph)
        pre_ref = snapshot_ref(current_graph)
        pre_compromised = _count_compromised(current_graph)

        red_legal_actions = get_legal_actions(current_graph, "red")
        if not red_legal_actions:
            raise RuntimeError("no legal actions available for red actor")

        red_decision: PolicyDecision | None = None
        if selector is None and runtime_policy_registry.has(ActorType.RED):
            red_context = _build_policy_context(
                actor=ActorType.RED,
                timestep=timestep,
                scenario_id=scenario_id,
                seed=seed,
                graph=current_graph,
                metrics_snapshot=red_metrics,
            )
            red_decision = runtime_policy_registry.get(ActorType.RED).select_action(red_context, red_legal_actions)
            red_action = red_decision.action
            red_metrics = red_decision.metrics_snapshot
        else:
            red_action = policy_selector("red", red_legal_actions, rng, timestep)

        resistance_rng = rng if exploit_resistance else None
        after_red_graph, red_result = _apply_red_action(current_graph, red_action, rng=resistance_rng)

        blue_legal_actions = get_legal_actions(after_red_graph, "blue")
        if not blue_legal_actions:
            raise RuntimeError("no legal actions available for blue actor")

        blue_decision: PolicyDecision | None = None
        if selector is None and runtime_policy_registry.has(ActorType.BLUE):
            blue_context = _build_policy_context(
                actor=ActorType.BLUE,
                timestep=timestep,
                scenario_id=scenario_id,
                seed=seed,
                graph=after_red_graph,
                metrics_snapshot=blue_metrics,
            )
            blue_decision = runtime_policy_registry.get(ActorType.BLUE).select_action(blue_context, blue_legal_actions)
            blue_action = blue_decision.action
            blue_metrics = blue_decision.metrics_snapshot
        else:
            blue_action = policy_selector("blue", blue_legal_actions, rng, timestep)

        after_blue_graph, blue_result = _apply_blue_action(after_red_graph, blue_action)

        post_payload = snapshot_payload(after_blue_graph)
        post_compromised = _count_compromised(after_blue_graph)

        red_record = _to_action_record("red", red_action, red_result, red_decision)
        blue_record = _to_action_record("blue", blue_action, blue_result, blue_decision)

        policy_metrics_payload = {}
        if red_decision is not None:
            policy_metrics_payload["red"] = asdict(red_decision.metrics_snapshot)
        if blue_decision is not None:
            policy_metrics_payload["blue"] = asdict(blue_decision.metrics_snapshot)

        log_entry = TimestepLogEntry(
            timestep=timestep,
            pre_state_ref=pre_ref,
            post_state_ref=snapshot_ref(after_blue_graph),
            red_action_intent=red_record,
            blue_action_intent=blue_record,
            action_outcomes=(red_record, blue_record),
            post_state_diff=compute_post_state_diff(pre_payload, post_payload),
            metric_delta={
                "compromised_nodes_before": pre_compromised,
                "compromised_nodes_after": post_compromised,
                "compromised_nodes_delta": post_compromised - pre_compromised,
                "policy_metrics": policy_metrics_payload,
            },
        )
        timestep_logs.append(log_entry)
        current_graph = after_blue_graph
        turn_graphs.append(after_blue_graph.copy())

    metadata = RunMetadata(
        run_id=run_id,
        seed=seed,
        scenario_id=scenario_id,
        horizon=horizon,
        timestamp_utc=datetime.now(timezone.utc).isoformat(),
    )

    return SimulationRunResult(
        metadata=metadata,
        final_graph=current_graph,
        timesteps=tuple(timestep_logs),
        graph_snapshots=tuple(turn_graphs),
    )
