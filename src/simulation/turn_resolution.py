from __future__ import annotations

import networkx as nx

from environment.legal_actions import LegalAction
from environment.transitions import (
    TransitionResult,
    apply_block,
    apply_deploy_decoy,
    apply_exploit,
    apply_feint,
    apply_isolate,
    apply_patch,
)
from hart.enums import ActionType, ActorType, parse_actor


def count_compromised_nodes(graph: nx.Graph) -> int:
    total = 0
    for _, attrs in graph.nodes(data=True):
        if attrs.get("compromised_state") in {"user", "privileged"}:
            total += 1
    return total


def apply_actor_action(
    graph: nx.Graph,
    actor: ActorType | str,
    action: LegalAction,
) -> tuple[nx.Graph, TransitionResult]:
    normalized_actor = parse_actor(actor)

    if normalized_actor == ActorType.RED:
        if action.action_type == ActionType.EXPLOIT:
            return apply_exploit(graph, action.targets[0])
        if action.action_type == ActionType.ESCALATE:
            return apply_exploit(graph, action.targets[0])
        if action.action_type == ActionType.LATERAL_MOVE:
            return apply_exploit(graph, action.targets[1])
    else:
        if action.action_type == ActionType.PATCH:
            return apply_patch(graph, action.targets[0])
        if action.action_type == ActionType.ISOLATE:
            return apply_isolate(graph, action.targets[0])
        if action.action_type == ActionType.BLOCK:
            return apply_block(graph, action.targets[0], action.targets[1])
        if action.action_type == ActionType.DECOY:
            return apply_deploy_decoy(graph, action.targets[0])
        if action.action_type == ActionType.FEINT:
            return apply_feint(graph, action.targets[0])

    return graph.copy(), TransitionResult(
        action=action.action_type.value,
        target=":".join(action.targets),
        changed=False,
        reason="no state mutation for informational action",
    )
