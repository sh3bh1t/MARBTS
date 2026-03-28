from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping

from schemas.scenario import ScenarioConfig


@dataclass(frozen=True)
class NodeRuntimeState:
    node_id: str
    security_level: int
    compromised_state: str
    detection_state: str
    isolation_state: bool


@dataclass(frozen=True)
class SimulationState:
    scenario_id: str
    timestep: int
    nodes: Mapping[str, NodeRuntimeState]


def initialize_simulation_state(scenario: ScenarioConfig) -> SimulationState:
    node_map = {
        node.node_id: NodeRuntimeState(
            node_id=node.node_id,
            security_level=node.security_level,
            compromised_state=node.compromised_state.value,
            detection_state=node.detection_state.value,
            isolation_state=node.isolation_state,
        )
        for node in scenario.nodes
    }

    return SimulationState(
        scenario_id=scenario.metadata.scenario_id,
        timestep=0,
        nodes=node_map,
    )
