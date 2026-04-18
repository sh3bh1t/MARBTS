from __future__ import annotations

import copy

import networkx as nx
from hart.enums import CompromisedState
from hart.models import TransitionResult


_COMPROMISE_LEVELS = (
    CompromisedState.NONE.value,
    CompromisedState.USER.value,
    CompromisedState.PRIVILEGED.value,
)
_MAX_SECURITY_LEVEL = 10


def _clone_graph(graph: nx.Graph) -> nx.Graph:
    cloned = nx.Graph()

    for node_id, attrs in graph.nodes(data=True):
        cloned.add_node(node_id, **copy.deepcopy(attrs))

    for source, target, attrs in graph.edges(data=True):
        cloned.add_edge(source, target, **copy.deepcopy(attrs))

    return cloned


def _ensure_node_exists(graph: nx.Graph, node_id: str, action_name: str) -> None:
    if node_id not in graph:
        raise ValueError(f"{action_name}: unknown node '{node_id}'")


def apply_exploit(graph: nx.Graph, node_id: str) -> tuple[nx.Graph, TransitionResult]:
    _ensure_node_exists(graph, node_id, "exploit")
    next_graph = _clone_graph(graph)

    if next_graph.nodes[node_id].get("isolation_state") is True:
        return next_graph, TransitionResult(
            action="exploit",
            target=node_id,
            changed=False,
            reason="node is isolated",
        )

    if next_graph.nodes[node_id].get("decoy_state") is True:
        next_graph.nodes[node_id]["detection_state"] = "confirmed"
        next_graph.nodes[node_id]["decoy_state"] = False
        return next_graph, TransitionResult(
            action="exploit",
            target=node_id,
            changed=True,
            reason="decoy absorbed exploit attempt and triggered defender visibility",
            details={
                "deception_triggered": True,
                "deception_type": "decoy",
                "detection_state": "confirmed",
            },
        )

    if next_graph.nodes[node_id].get("feint_state") is True:
        next_graph.nodes[node_id]["detection_state"] = "suspected"
        next_graph.nodes[node_id]["feint_state"] = False
        return next_graph, TransitionResult(
            action="exploit",
            target=node_id,
            changed=True,
            reason="feint diverted exploit attempt and generated partial defender visibility",
            details={
                "deception_triggered": True,
                "deception_type": "feint",
                "detection_state": "suspected",
            },
        )

    current_state = next_graph.nodes[node_id]["compromised_state"]
    current_idx = _COMPROMISE_LEVELS.index(current_state)
    if current_idx == len(_COMPROMISE_LEVELS) - 1:
        return next_graph, TransitionResult(
            action="exploit",
            target=node_id,
            changed=False,
            reason="already at maximum compromise level",
        )

    next_graph.nodes[node_id]["compromised_state"] = _COMPROMISE_LEVELS[current_idx + 1]
    return next_graph, TransitionResult(
        action="exploit",
        target=node_id,
        changed=True,
        reason="compromise level increased by one",
    )


def apply_patch(graph: nx.Graph, node_id: str) -> tuple[nx.Graph, TransitionResult]:
    _ensure_node_exists(graph, node_id, "patch")
    next_graph = _clone_graph(graph)

    changed = False
    reasons: list[str] = []

    current_security_level = next_graph.nodes[node_id]["security_level"]
    if current_security_level < _MAX_SECURITY_LEVEL:
        next_graph.nodes[node_id]["security_level"] = current_security_level + 1
        changed = True
        reasons.append("security level +1")

    current_state = next_graph.nodes[node_id]["compromised_state"]
    current_idx = _COMPROMISE_LEVELS.index(current_state)
    if current_idx > 0:
        next_graph.nodes[node_id]["compromised_state"] = _COMPROMISE_LEVELS[current_idx - 1]
        changed = True
        reasons.append("compromise level reduced by one")

    vulnerabilities = next_graph.nodes[node_id].get("vulnerabilities", [])
    if vulnerabilities:
        vulnerabilities.pop(0)
        changed = True
        reasons.append("removed one vulnerability")

    if not changed:
        reasons.append("no mutable fields eligible for patch")

    return next_graph, TransitionResult(
        action="patch",
        target=node_id,
        changed=changed,
        reason="; ".join(reasons),
    )


def apply_isolate(graph: nx.Graph, node_id: str) -> tuple[nx.Graph, TransitionResult]:
    _ensure_node_exists(graph, node_id, "isolate")
    next_graph = _clone_graph(graph)

    already_isolated = next_graph.nodes[node_id].get("isolation_state") is True
    next_graph.nodes[node_id]["isolation_state"] = True

    removed_edges = list(next_graph.edges(node_id))
    next_graph.remove_edges_from(removed_edges)

    changed = (not already_isolated) or bool(removed_edges)
    return next_graph, TransitionResult(
        action="isolate",
        target=node_id,
        changed=changed,
        reason=f"isolation set true; removed {len(removed_edges)} connected edges",
    )


def apply_block(graph: nx.Graph, source: str, target: str) -> tuple[nx.Graph, TransitionResult]:
    _ensure_node_exists(graph, source, "block")
    _ensure_node_exists(graph, target, "block")
    next_graph = _clone_graph(graph)

    if not next_graph.has_edge(source, target):
        return next_graph, TransitionResult(
            action="block",
            target=f"{source}->{target}",
            changed=False,
            reason="edge does not exist",
        )

    next_graph.remove_edge(source, target)
    return next_graph, TransitionResult(
        action="block",
        target=f"{source}->{target}",
        changed=True,
        reason="edge removed",
    )


def apply_deploy_decoy(graph: nx.Graph, node_id: str) -> tuple[nx.Graph, TransitionResult]:
    _ensure_node_exists(graph, node_id, "decoy")
    next_graph = _clone_graph(graph)

    if next_graph.nodes[node_id].get("decoy_state") is True:
        return next_graph, TransitionResult(
            action="decoy",
            target=node_id,
            changed=False,
            reason="decoy already active",
            details={"decoy_deployed": False},
        )

    next_graph.nodes[node_id]["decoy_state"] = True
    return next_graph, TransitionResult(
        action="decoy",
        target=node_id,
        changed=True,
        reason="decoy deployed on node",
        details={"decoy_deployed": True, "deception_type": "decoy"},
    )


def apply_feint(graph: nx.Graph, node_id: str) -> tuple[nx.Graph, TransitionResult]:
    _ensure_node_exists(graph, node_id, "feint")
    next_graph = _clone_graph(graph)

    if next_graph.nodes[node_id].get("feint_state") is True:
        return next_graph, TransitionResult(
            action="feint",
            target=node_id,
            changed=False,
            reason="feint already active",
            details={"feint_deployed": False},
        )

    next_graph.nodes[node_id]["feint_state"] = True
    return next_graph, TransitionResult(
        action="feint",
        target=node_id,
        changed=True,
        reason="feint signal deployed on node",
        details={"feint_deployed": True, "deception_type": "feint"},
    )
