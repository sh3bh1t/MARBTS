from __future__ import annotations

from dataclasses import dataclass, field
from typing import Mapping

from hart.enums import ActionType, ActorType


@dataclass(frozen=True)
class NodeRuntimeState:
    node_id: str
    security_level: int
    compromised_state: str
    detection_state: str
    isolation_state: bool
    decoy_state: bool = False
    feint_state: bool = False


@dataclass(frozen=True)
class SimulationState:
    scenario_id: str
    timestep: int
    nodes: Mapping[str, NodeRuntimeState]


@dataclass(frozen=True)
class LegalAction:
    actor: ActorType
    action_type: ActionType
    targets: tuple[str, ...]
    rationale_hint: str


@dataclass(frozen=True)
class TransitionResult:
    action: str
    target: str
    changed: bool
    reason: str
    details: Mapping[str, object] = field(default_factory=dict)
