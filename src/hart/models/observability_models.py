from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping


@dataclass(frozen=True)
class RunProvenance:
    run_id: str
    seed: int
    scenario_id: str
    scenario_version: str
    horizon: int
    config_hash: str
    commit_hash: str
    code_version: str
    timestamp_utc: str


@dataclass(frozen=True)
class EventEnvelope:
    schema_version: str
    event_type: str
    event_id: str
    provenance: RunProvenance
    payload: Mapping[str, object]


@dataclass(frozen=True)
class ReplayFrame:
    timestep: int
    state_ref: str
    state_snapshot: Mapping[str, object]
