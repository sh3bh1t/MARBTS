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
from environment.transitions import TransitionResult
from hart.enums import ActorType
from hart.models import ActionRecord, PolicyContext, PolicyMetricsSnapshot, RunMetadata, SimulationRunResult, TimestepLogEntry
from simulation.provenance import compute_config_hash, detect_git_commit_hash
from simulation.rng import SeededRNG
from simulation.state_diff import compute_post_state_diff, snapshot_payload, snapshot_ref
from simulation.turn_resolution import apply_actor_action, count_compromised_nodes


ActionSelector = Callable[[str, tuple[LegalAction, ...], SeededRNG, int], LegalAction]


def _build_default_policy_registry() -> PolicyRegistry:
    registry = PolicyRegistry()
    registry.register(RuleBasedRedPolicy())
    registry.register(RuleBasedBluePolicy())
    return registry


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
    predicted_effect = ""
    confidence = 0.0
    utility_estimate = 0.0
    decision_trace: dict = {}

    if policy_decision is not None:
        rationale = policy_decision.rationale.summary
        rationale_payload = asdict(policy_decision.rationale)
        predicted_effect = policy_decision.rationale.predicted_effect
        confidence = policy_decision.rationale.confidence
        utility_estimate = policy_decision.rationale.utility_estimate
        decision_trace = dict(policy_decision.rationale.trace)

    return ActionRecord(
        actor=actor,
        action_type=legal_action.action_type.value,
        targets=legal_action.targets,
        rationale=rationale,
        rationale_payload=rationale_payload,
        changed=transition.changed,
        reason=transition.reason,
        predicted_effect=predicted_effect,
        confidence=confidence,
        utility_estimate=utility_estimate,
        decision_trace=decision_trace,
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
        compromised_nodes=count_compromised_nodes(graph),
        policy_metrics=policy_metrics,
        state_snapshot=snapshot_payload(graph),
    )


def run_turn_based_simulation(
    initial_graph: nx.Graph,
    *,
    seed: int,
    horizon: int,
    scenario_id: str,
    scenario_version: str = "unknown",
    config_payload: dict | None = None,
    commit_hash: str | None = None,
    selector: ActionSelector | None = None,
    policy_registry: PolicyRegistry | None = None,
) -> SimulationRunResult:
    if horizon < 1:
        raise ValueError("horizon must be >= 1")

    policy_selector = selector or _default_selector
    runtime_policy_registry = policy_registry or _build_default_policy_registry()
    rng = SeededRNG(seed)

    current_graph = initial_graph.copy()
    timestep_logs: list[TimestepLogEntry] = []
    initial_state_ref = snapshot_ref(current_graph)

    run_id_input = f"{scenario_id}:{seed}:{horizon}:{initial_state_ref}"
    run_id = hashlib.sha256(run_id_input.encode("utf-8")).hexdigest()[:16]
    resolved_commit_hash = commit_hash or detect_git_commit_hash()
    resolved_config_hash = compute_config_hash(config_payload or snapshot_payload(current_graph))

    red_metrics: PolicyMetricsSnapshot | None = None
    blue_metrics: PolicyMetricsSnapshot | None = None

    for timestep in range(horizon):
        pre_payload = snapshot_payload(current_graph)
        pre_ref = snapshot_ref(current_graph)
        pre_compromised = count_compromised_nodes(current_graph)

        red_legal_actions = get_legal_actions(current_graph, "red")
        if not red_legal_actions:
            break

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

        after_red_graph, red_result = apply_actor_action(current_graph, ActorType.RED, red_action)

        blue_legal_actions = get_legal_actions(after_red_graph, "blue")
        if not blue_legal_actions:
            break

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

        after_blue_graph, blue_result = apply_actor_action(after_red_graph, ActorType.BLUE, blue_action)

        post_payload = snapshot_payload(after_blue_graph)
        post_ref = snapshot_ref(after_blue_graph)
        post_compromised = count_compromised_nodes(after_blue_graph)

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
            post_state_ref=post_ref,
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

    metadata = RunMetadata(
        run_id=run_id,
        seed=seed,
        scenario_id=scenario_id,
        scenario_version=scenario_version,
        horizon=horizon,
        config_hash=resolved_config_hash,
        commit_hash=resolved_commit_hash,
        code_version="workspace",
        timestamp_utc=datetime.now(timezone.utc).isoformat(),
        initial_state_ref=initial_state_ref,
        final_state_ref=snapshot_ref(current_graph),
    )

    return SimulationRunResult(
        metadata=metadata,
        initial_graph=initial_graph.copy(),
        final_graph=current_graph,
        timesteps=tuple(timestep_logs),
    )
