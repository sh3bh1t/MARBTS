from __future__ import annotations

from dataclasses import dataclass

import networkx as nx


@dataclass(frozen=True)
class RunMetadata:
    run_id: str
    seed: int
    scenario_id: str
    horizon: int
    timestamp_utc: str


@dataclass(frozen=True)
class ActionRecord:
    actor: str
    action_type: str
    targets: tuple[str, ...]
    rationale: str
    rationale_payload: dict
    changed: bool
    reason: str


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
    final_graph: nx.Graph
    timesteps: tuple[TimestepLogEntry, ...]
