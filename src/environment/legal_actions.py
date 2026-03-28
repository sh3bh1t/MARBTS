from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

import networkx as nx

Actor = Literal["red", "blue"]


@dataclass(frozen=True)
class LegalAction:
    actor: Actor
    action_type: str
    targets: tuple[str, ...]
    rationale_hint: str


def _sorted_edges(graph: nx.Graph) -> list[tuple[str, str]]:
    normalized = [tuple(sorted((source, target))) for source, target in graph.edges()]
    return sorted(set(normalized))


def _is_compromised(node_attrs: dict) -> bool:
    return node_attrs.get("compromised_state") in {"user", "privileged"}


def get_legal_actions(graph: nx.Graph, actor: Actor) -> tuple[LegalAction, ...]:
    if actor not in {"red", "blue"}:
        raise ValueError(f"unsupported actor '{actor}'")

    actions: list[LegalAction] = []

    if actor == "red":
        for node_id in sorted(graph.nodes()):
            attrs = graph.nodes[node_id]
            if attrs.get("isolation_state"):
                continue

            actions.append(
                LegalAction(
                    actor="red",
                    action_type="scan",
                    targets=(node_id,),
                    rationale_hint="discover node exposure and service surface",
                )
            )

            if attrs.get("vulnerabilities") and attrs.get("compromised_state") != "privileged":
                actions.append(
                    LegalAction(
                        actor="red",
                        action_type="exploit",
                        targets=(node_id,),
                        rationale_hint="advance compromise level on vulnerable target",
                    )
                )

            if attrs.get("compromised_state") == "user":
                actions.append(
                    LegalAction(
                        actor="red",
                        action_type="escalate",
                        targets=(node_id,),
                        rationale_hint="escalate local privileges from user to privileged",
                    )
                )

        for source in sorted(graph.nodes()):
            source_attrs = graph.nodes[source]
            if source_attrs.get("isolation_state") or not _is_compromised(source_attrs):
                continue

            for target in sorted(graph.neighbors(source)):
                target_attrs = graph.nodes[target]
                if target_attrs.get("isolation_state"):
                    continue
                if target_attrs.get("compromised_state") == "privileged":
                    continue
                actions.append(
                    LegalAction(
                        actor="red",
                        action_type="lateral_move",
                        targets=(source, target),
                        rationale_hint="expand foothold through reachable neighbor",
                    )
                )

    if actor == "blue":
        for node_id in sorted(graph.nodes()):
            attrs = graph.nodes[node_id]
            actions.append(
                LegalAction(
                    actor="blue",
                    action_type="monitor",
                    targets=(node_id,),
                    rationale_hint="observe node state and detect compromise indicators",
                )
            )

            patchable = bool(attrs.get("vulnerabilities")) or attrs.get("compromised_state") != "none" or attrs.get("security_level", 0) < 10
            if patchable:
                actions.append(
                    LegalAction(
                        actor="blue",
                        action_type="patch",
                        targets=(node_id,),
                        rationale_hint="reduce vulnerability and compromise exposure",
                    )
                )

            if not attrs.get("isolation_state"):
                actions.append(
                    LegalAction(
                        actor="blue",
                        action_type="isolate",
                        targets=(node_id,),
                        rationale_hint="contain possible lateral movement from/to node",
                    )
                )

        for source, target in _sorted_edges(graph):
            actions.append(
                LegalAction(
                    actor="blue",
                    action_type="block",
                    targets=(source, target),
                    rationale_hint="remove network path to reduce attack propagation",
                )
            )

    return tuple(actions)
