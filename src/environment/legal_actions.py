from __future__ import annotations

import networkx as nx

from hart.enums import ActionType, ActorType, parse_actor
from hart.models import LegalAction


def _sorted_edges(graph: nx.Graph) -> list[tuple[str, str]]:
    normalized = [tuple(sorted((source, target))) for source, target in graph.edges()]
    return sorted(set(normalized))


def _is_compromised(node_attrs: dict) -> bool:
    return node_attrs.get("compromised_state") in {"user", "privileged"}


def get_legal_actions(graph: nx.Graph, actor: ActorType | str) -> tuple[LegalAction, ...]:
    try:
        normalized_actor = parse_actor(actor)
    except ValueError as exc:
        raise ValueError(f"unsupported actor '{actor}'") from exc

    actions: list[LegalAction] = []

    if normalized_actor == ActorType.RED:
        for node_id in sorted(graph.nodes()):
            attrs = graph.nodes[node_id]
            if attrs.get("isolation_state"):
                continue
            sec_level = int(attrs.get("security_level", 1))

            actions.append(
                LegalAction(
                    actor=ActorType.RED,
                    action_type=ActionType.SCAN,
                    targets=(node_id,),
                    rationale_hint="discover node exposure and service surface",
                    node_security_level=sec_level,
                )
            )

            if attrs.get("vulnerabilities") and attrs.get("compromised_state") != "privileged":
                actions.append(
                    LegalAction(
                        actor=ActorType.RED,
                        action_type=ActionType.EXPLOIT,
                        targets=(node_id,),
                        rationale_hint="advance compromise level on vulnerable target",
                        node_security_level=sec_level,
                    )
                )

            if attrs.get("compromised_state") == "user":
                actions.append(
                    LegalAction(
                        actor=ActorType.RED,
                        action_type=ActionType.ESCALATE,
                        targets=(node_id,),
                        rationale_hint="escalate local privileges from user to privileged",
                        node_security_level=sec_level,
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
                        actor=ActorType.RED,
                        action_type=ActionType.LATERAL_MOVE,
                        targets=(source, target),
                        rationale_hint="expand foothold through reachable neighbor",
                        node_security_level=int(target_attrs.get("security_level", 1)),
                    )
                )

    if normalized_actor == ActorType.BLUE:
        for node_id in sorted(graph.nodes()):
            attrs = graph.nodes[node_id]
            sec_level = int(attrs.get("security_level", 1))
            actions.append(
                LegalAction(
                    actor=ActorType.BLUE,
                    action_type=ActionType.MONITOR,
                    targets=(node_id,),
                    rationale_hint="observe node state and detect compromise indicators",
                    node_security_level=sec_level,
                )
            )

            patchable = bool(attrs.get("vulnerabilities")) or attrs.get("compromised_state") != "none" or attrs.get("security_level", 0) < 10
            if patchable:
                actions.append(
                    LegalAction(
                        actor=ActorType.BLUE,
                        action_type=ActionType.PATCH,
                        targets=(node_id,),
                        rationale_hint="reduce vulnerability and compromise exposure",
                        node_security_level=sec_level,
                    )
                )

            if not attrs.get("isolation_state"):
                actions.append(
                    LegalAction(
                        actor=ActorType.BLUE,
                        action_type=ActionType.ISOLATE,
                        targets=(node_id,),
                        rationale_hint="contain possible lateral movement from/to node",
                        node_security_level=sec_level,
                    )
                )

        for source, target in _sorted_edges(graph):
            target_sec = int(graph.nodes[target].get("security_level", 1))
            actions.append(
                LegalAction(
                    actor=ActorType.BLUE,
                    action_type=ActionType.BLOCK,
                    targets=(source, target),
                    rationale_hint="remove network path to reduce attack propagation",
                    node_security_level=target_sec,
                )
            )

    return tuple(actions)
