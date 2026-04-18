from __future__ import annotations

from dataclasses import dataclass, field

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


@dataclass(frozen=True)
class ScenarioCatalogEntry:
    scenario_id: str
    version: str
    path: str
    tags: tuple[str, ...] = ()
    topology_complexity: str = "unknown"
    vulnerability_density: str = "unknown"
    defense_posture: str = "unknown"


@dataclass(frozen=True)
class StressTestConfig:
    config_id: str
    scenario_ids: tuple[str, ...]
    seeds: tuple[int, ...]
    horizon: int
    planner_depth: int = 3
    include_llm_conditions: bool = True
    feature_flags: dict[str, bool] = field(default_factory=dict)
