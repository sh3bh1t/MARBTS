from __future__ import annotations

from dataclasses import dataclass
import copy

import networkx as nx


_COMPROMISE_LEVELS = ("none", "user", "privileged")
_MAX_SECURITY_LEVEL = 10


@dataclass(frozen=True)
class TransitionResult:
    action: str
    target: str
    changed: bool
    reason: str


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
