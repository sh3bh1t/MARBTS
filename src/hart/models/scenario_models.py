from __future__ import annotations

from dataclasses import dataclass

from hart.enums import CompromisedState, DetectionState, NodeType


@dataclass(frozen=True)
class NodeConfig:
    node_id: str
    node_type: NodeType
    services: tuple[str, ...]
    vulnerabilities: tuple[str, ...]
    security_level: int
    compromised_state: CompromisedState
    detection_state: DetectionState
    isolation_state: bool


@dataclass(frozen=True)
class EdgeConfig:
    source: str
    target: str


@dataclass(frozen=True)
class ScenarioMetadata:
    scenario_id: str
    version: str


@dataclass(frozen=True)
class ScenarioConfig:
    metadata: ScenarioMetadata
    nodes: tuple[NodeConfig, ...]
    edges: tuple[EdgeConfig, ...]

    @property
    def node_ids(self) -> tuple[str, ...]:
        return tuple(node.node_id for node in self.nodes)
