from __future__ import annotations

import networkx as nx

from schemas.scenario import ScenarioConfig


def build_graph_from_scenario(scenario: ScenarioConfig) -> nx.Graph:
    graph = nx.Graph()

    for node in scenario.nodes:
        graph.add_node(
            node.node_id,
            node_type=node.node_type.value,
            services=list(node.services),
            vulnerabilities=list(node.vulnerabilities),
            security_level=node.security_level,
            compromised_state=node.compromised_state.value,
            detection_state=node.detection_state.value,
            isolation_state=node.isolation_state,
            decoy_state=False,
            feint_state=False,
        )

    for edge in scenario.edges:
        graph.add_edge(edge.source, edge.target)

    return graph
