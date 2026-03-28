from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import hashlib
from typing import Callable

import networkx as nx

from environment.legal_actions import LegalAction, get_legal_actions
from environment.transitions import TransitionResult, apply_block, apply_exploit, apply_isolate, apply_patch
from simulation.rng import SeededRNG
from simulation.state_diff import compute_post_state_diff, snapshot_payload, snapshot_ref


@dataclass(frozen=True)
class RunMetadata:
    run_id: str
    seed: int
    scenario_id: str
    horizon: int
    timestamp_utc: str


@dataclass(frozen=True)
class ActionRecord:
    actor: str
    action_type: str
    targets: tuple[str, ...]
    rationale: str
    changed: bool
    reason: str


@dataclass(frozen=True)
class TimestepLogEntry:
    timestep: int
    pre_state_ref: str
    red_action_intent: ActionRecord
    blue_action_intent: ActionRecord
    action_outcomes: tuple[ActionRecord, ActionRecord]
    post_state_diff: dict
    metric_delta: dict


@dataclass(frozen=True)
class SimulationRunResult:
    metadata: RunMetadata
    final_graph: nx.Graph
    timesteps: tuple[TimestepLogEntry, ...]


ActionSelector = Callable[[str, tuple[LegalAction, ...], SeededRNG, int], LegalAction]


def _count_compromised(graph: nx.Graph) -> int:
    total = 0
    for _, attrs in graph.nodes(data=True):
        if attrs.get("compromised_state") in {"user", "privileged"}:
            total += 1
    return total


def _apply_red_action(graph: nx.Graph, action: LegalAction) -> tuple[nx.Graph, TransitionResult]:
    if action.action_type == "exploit":
        return apply_exploit(graph, action.targets[0])

    if action.action_type == "escalate":
        return apply_exploit(graph, action.targets[0])

    if action.action_type == "lateral_move":
        return apply_exploit(graph, action.targets[1])

    return graph, TransitionResult(
        action=action.action_type,
        target=":".join(action.targets),
        changed=False,
        reason="no state mutation for informational action",
    )


def _apply_blue_action(graph: nx.Graph, action: LegalAction) -> tuple[nx.Graph, TransitionResult]:
    if action.action_type == "patch":
        return apply_patch(graph, action.targets[0])

    if action.action_type == "isolate":
        return apply_isolate(graph, action.targets[0])

    if action.action_type == "block":
        return apply_block(graph, action.targets[0], action.targets[1])

    return graph, TransitionResult(
        action=action.action_type,
        target=":".join(action.targets),
        changed=False,
        reason="no state mutation for informational action",
    )


def _default_selector(_actor: str, legal_actions: tuple[LegalAction, ...], rng: SeededRNG, _timestep: int) -> LegalAction:
    return rng.choice(legal_actions)


def _to_action_record(actor: str, legal_action: LegalAction, transition: TransitionResult) -> ActionRecord:
    return ActionRecord(
        actor=actor,
        action_type=legal_action.action_type,
        targets=legal_action.targets,
        rationale=legal_action.rationale_hint,
        changed=transition.changed,
        reason=transition.reason,
    )


def run_turn_based_simulation(
    initial_graph: nx.Graph,
    *,
    seed: int,
    horizon: int,
    scenario_id: str,
    selector: ActionSelector | None = None,
) -> SimulationRunResult:
    if horizon < 1:
        raise ValueError("horizon must be >= 1")

    policy_selector = selector or _default_selector
    rng = SeededRNG(seed)

    current_graph = initial_graph.copy()
    timestep_logs: list[TimestepLogEntry] = []

    run_id_input = f"{scenario_id}:{seed}:{horizon}:{snapshot_ref(current_graph)}"
    run_id = hashlib.sha256(run_id_input.encode("utf-8")).hexdigest()[:16]

    for timestep in range(horizon):
        pre_payload = snapshot_payload(current_graph)
        pre_ref = snapshot_ref(current_graph)
        pre_compromised = _count_compromised(current_graph)

        red_legal_actions = get_legal_actions(current_graph, "red")
        if not red_legal_actions:
            raise RuntimeError("no legal actions available for red actor")
        red_action = policy_selector("red", red_legal_actions, rng, timestep)
        after_red_graph, red_result = _apply_red_action(current_graph, red_action)

        blue_legal_actions = get_legal_actions(after_red_graph, "blue")
        if not blue_legal_actions:
            raise RuntimeError("no legal actions available for blue actor")
        blue_action = policy_selector("blue", blue_legal_actions, rng, timestep)
        after_blue_graph, blue_result = _apply_blue_action(after_red_graph, blue_action)

        post_payload = snapshot_payload(after_blue_graph)
        post_compromised = _count_compromised(after_blue_graph)

        red_record = _to_action_record("red", red_action, red_result)
        blue_record = _to_action_record("blue", blue_action, blue_result)

        log_entry = TimestepLogEntry(
            timestep=timestep,
            pre_state_ref=pre_ref,
            red_action_intent=red_record,
            blue_action_intent=blue_record,
            action_outcomes=(red_record, blue_record),
            post_state_diff=compute_post_state_diff(pre_payload, post_payload),
            metric_delta={
                "compromised_nodes_before": pre_compromised,
                "compromised_nodes_after": post_compromised,
                "compromised_nodes_delta": post_compromised - pre_compromised,
            },
        )
        timestep_logs.append(log_entry)
        current_graph = after_blue_graph

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
    )
