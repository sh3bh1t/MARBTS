from __future__ import annotations

import hashlib
import json

import networkx as nx


def snapshot_payload(graph: nx.Graph) -> dict:
    nodes = {}
    for node_id in sorted(graph.nodes()):
        attrs = graph.nodes[node_id]
        nodes[node_id] = {
            "node_type": attrs.get("node_type"),
            "services": list(attrs.get("services", [])),
            "vulnerabilities": list(attrs.get("vulnerabilities", [])),
            "security_level": attrs.get("security_level"),
            "compromised_state": attrs.get("compromised_state"),
            "detection_state": attrs.get("detection_state"),
            "isolation_state": attrs.get("isolation_state"),
        }

    edges = [tuple(sorted((source, target))) for source, target in graph.edges()]
    edges = sorted(set(edges))

    return {"nodes": nodes, "edges": edges}


def snapshot_ref(graph: nx.Graph) -> str:
    payload = snapshot_payload(graph)
    encoded = json.dumps(payload, sort_keys=True).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def compute_post_state_diff(pre_payload: dict, post_payload: dict) -> dict:
    changed_nodes: list[dict] = []

    pre_nodes = pre_payload["nodes"]
    post_nodes = post_payload["nodes"]
    for node_id in sorted(pre_nodes.keys()):
        if pre_nodes[node_id] != post_nodes[node_id]:
            changed_nodes.append(
                {
                    "node_id": node_id,
                    "before": pre_nodes[node_id],
                    "after": post_nodes[node_id],
                }
            )

    pre_edges = set(tuple(edge) for edge in pre_payload["edges"])
    post_edges = set(tuple(edge) for edge in post_payload["edges"])

    return {
        "changed_nodes": changed_nodes,
        "removed_edges": sorted(pre_edges - post_edges),
        "added_edges": sorted(post_edges - pre_edges),
    }
