from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
import json
from pathlib import Path
from typing import Any


class NodeType(str, Enum):
    SERVER = "server"
    DATABASE = "database"
    IOT = "iot"
    ENDPOINT = "endpoint"


class CompromisedState(str, Enum):
    NONE = "none"
    USER = "user"
    PRIVILEGED = "privileged"


class DetectionState(str, Enum):
    UNDETECTED = "undetected"
    SUSPECTED = "suspected"
    CONFIRMED = "confirmed"


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


_REQUIRED_NODE_FIELDS = {
    "node_id",
    "node_type",
    "services",
    "vulnerabilities",
    "security_level",
    "compromised_state",
    "detection_state",
    "isolation_state",
}


def _ensure_field(obj: dict[str, Any], field_name: str, context: str) -> Any:
    if field_name not in obj:
        raise ValueError(f"{context}: missing required field '{field_name}'")
    return obj[field_name]


def _parse_node(node_obj: dict[str, Any]) -> NodeConfig:
    missing = _REQUIRED_NODE_FIELDS.difference(node_obj.keys())
    if missing:
        missing_names = ", ".join(sorted(missing))
        raise ValueError(f"node '{node_obj.get('node_id', '<unknown>')}': missing required fields: {missing_names}")

    node_id = str(_ensure_field(node_obj, "node_id", "node"))
    services_raw = _ensure_field(node_obj, "services", f"node '{node_id}'")
    vulnerabilities_raw = _ensure_field(node_obj, "vulnerabilities", f"node '{node_id}'")

    if not isinstance(services_raw, list) or not all(isinstance(item, str) for item in services_raw):
        raise ValueError(f"node '{node_id}': 'services' must be a list of strings")
    if not isinstance(vulnerabilities_raw, list) or not all(isinstance(item, str) for item in vulnerabilities_raw):
        raise ValueError(f"node '{node_id}': 'vulnerabilities' must be a list of strings")

    security_level = _ensure_field(node_obj, "security_level", f"node '{node_id}'")
    if not isinstance(security_level, int) or security_level < 0:
        raise ValueError(f"node '{node_id}': 'security_level' must be a non-negative integer")

    compromised_state = CompromisedState(_ensure_field(node_obj, "compromised_state", f"node '{node_id}'"))
    detection_state = DetectionState(_ensure_field(node_obj, "detection_state", f"node '{node_id}'"))

    isolation_state = _ensure_field(node_obj, "isolation_state", f"node '{node_id}'")
    if not isinstance(isolation_state, bool):
        raise ValueError(f"node '{node_id}': 'isolation_state' must be a boolean")

    return NodeConfig(
        node_id=node_id,
        node_type=NodeType(_ensure_field(node_obj, "node_type", f"node '{node_id}'")),
        services=tuple(services_raw),
        vulnerabilities=tuple(vulnerabilities_raw),
        security_level=security_level,
        compromised_state=compromised_state,
        detection_state=detection_state,
        isolation_state=isolation_state,
    )


def _parse_edge(edge_obj: dict[str, Any]) -> EdgeConfig:
    source = _ensure_field(edge_obj, "source", "edge")
    target = _ensure_field(edge_obj, "target", "edge")

    if not isinstance(source, str) or not source:
        raise ValueError("edge: 'source' must be a non-empty string")
    if not isinstance(target, str) or not target:
        raise ValueError("edge: 'target' must be a non-empty string")

    return EdgeConfig(source=source, target=target)


def validate_scenario_dict(data: dict[str, Any]) -> ScenarioConfig:
    metadata_obj = _ensure_field(data, "metadata", "scenario")
    nodes_obj = _ensure_field(data, "nodes", "scenario")
    edges_obj = _ensure_field(data, "edges", "scenario")

    if not isinstance(metadata_obj, dict):
        raise ValueError("scenario: 'metadata' must be an object")
    if not isinstance(nodes_obj, list):
        raise ValueError("scenario: 'nodes' must be a list")
    if not isinstance(edges_obj, list):
        raise ValueError("scenario: 'edges' must be a list")

    scenario_id = _ensure_field(metadata_obj, "scenario_id", "scenario.metadata")
    version = _ensure_field(metadata_obj, "version", "scenario.metadata")
    if not isinstance(scenario_id, str) or not scenario_id:
        raise ValueError("scenario.metadata: 'scenario_id' must be a non-empty string")
    if not isinstance(version, str) or not version:
        raise ValueError("scenario.metadata: 'version' must be a non-empty string")

    nodes = tuple(_parse_node(node) for node in nodes_obj)
    node_ids = [node.node_id for node in nodes]
    if len(node_ids) != len(set(node_ids)):
        raise ValueError("scenario: duplicate node_id values are not allowed")

    edges = tuple(_parse_edge(edge) for edge in edges_obj)
    node_id_set = set(node_ids)
    for edge in edges:
        if edge.source not in node_id_set or edge.target not in node_id_set:
            raise ValueError(
                f"scenario: edge '{edge.source}' -> '{edge.target}' references undefined node_id"
            )

    return ScenarioConfig(
        metadata=ScenarioMetadata(scenario_id=scenario_id, version=version),
        nodes=nodes,
        edges=edges,
    )


def load_scenario_file(path: str | Path) -> ScenarioConfig:
    scenario_path = Path(path)
    with scenario_path.open("r", encoding="utf-8") as file_obj:
        payload = json.load(file_obj)

    if not isinstance(payload, dict):
        raise ValueError("scenario file root must be a JSON object")

    return validate_scenario_dict(payload)
