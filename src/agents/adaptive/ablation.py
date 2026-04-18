from __future__ import annotations

from typing import Mapping

from hart.models import AdaptivePolicyConfig


def apply_observability_filter(snapshot: Mapping[str, object], config: AdaptivePolicyConfig) -> dict[str, object]:
    visible_snapshot = {
        "nodes": {},
        "edges": list(snapshot.get("edges", [])),
    }

    reduced_observability = bool(config.feature_flags.get("reduced_observability", False))
    for node_id, node_state in dict(snapshot.get("nodes", {})).items():
        visible_node = dict(node_state)
        if reduced_observability:
            visible_node["services"] = []
            visible_node["vulnerabilities"] = []
            if visible_node.get("detection_state") == "undetected":
                visible_node["compromised_state"] = "none"
        visible_snapshot["nodes"][node_id] = visible_node

    return visible_snapshot


def effective_planning_depth(config: AdaptivePolicyConfig) -> int:
    if config.feature_flags.get("no_planning", False):
        return 0
    return max(int(config.planning_depth), 0)
