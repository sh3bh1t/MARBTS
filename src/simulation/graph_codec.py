from __future__ import annotations

import networkx as nx


def graph_from_snapshot_payload(payload: dict) -> nx.Graph:
    graph = nx.Graph()

    for node_id in sorted(payload.get("nodes", {})):
        graph.add_node(node_id, **dict(payload["nodes"][node_id]))

    for edge in payload.get("edges", []):
        if len(edge) != 2:
            raise ValueError(f"invalid edge payload: {edge!r}")
        graph.add_edge(edge[0], edge[1])

    return graph
