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


def apply_exploit(graph: nx.Graph, node_id: str, rng=None) -> tuple[nx.Graph, TransitionResult]:
    """Apply an exploit action.

    When *rng* is provided, exploit success is probabilistic and resisted by
    the node's security_level:  prob = max(0.10, 1.0 - (sec_level - 1) / 10.0).
    When *rng* is None (default), the exploit always succeeds as before.
    """
    _ensure_node_exists(graph, node_id, "exploit")
    next_graph = _clone_graph(graph)

    if next_graph.nodes[node_id].get("isolation_state") is True:
        return next_graph, TransitionResult(
            action="exploit",
            target=node_id,
            changed=False,
            reason="node is isolated",
        )

    if rng is not None:
        security_level = int(next_graph.nodes[node_id].get("security_level", 1))
        success_prob = max(0.25, 1.0 - (security_level - 1) / 10.0)
        if rng.random() > success_prob:
            return next_graph, TransitionResult(
                action="exploit",
                target=node_id,
                changed=False,
                reason=f"exploit resisted by security controls (sec_level={security_level}, threshold={success_prob:.2f})",
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
