from __future__ import annotations

from dataclasses import dataclass, field
from typing import Mapping

import networkx as nx


@dataclass(frozen=True)
class RunMetadata:
    run_id: str
    seed: int
    scenario_id: str
    scenario_version: str
    horizon: int
    config_hash: str
    commit_hash: str
    code_version: str
    timestamp_utc: str
    initial_state_ref: str
    final_state_ref: str = ""


@dataclass(frozen=True)
class ActionRecord:
    actor: str
    action_type: str
    targets: tuple[str, ...]
    rationale: str
    rationale_payload: dict
    changed: bool
    reason: str
    predicted_effect: str = ""
    confidence: float = 0.0
    utility_estimate: float = 0.0
    decision_trace: Mapping[str, object] = field(default_factory=dict)


@dataclass(frozen=True)
class TimestepLogEntry:
    timestep: int
    pre_state_ref: str
    post_state_ref: str
    red_action_intent: ActionRecord
    blue_action_intent: ActionRecord
    action_outcomes: tuple[ActionRecord, ActionRecord]
    post_state_diff: dict
    metric_delta: dict


@dataclass(frozen=True)
class SimulationRunResult:
    metadata: RunMetadata
    initial_graph: nx.Graph
    final_graph: nx.Graph
    timesteps: tuple[TimestepLogEntry, ...]
