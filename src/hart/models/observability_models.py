from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Mapping


OBSERVABILITY_SCHEMA_VERSION = "2026-04-23.observability.v1"
RUN_METADATA_EVENT_TYPE = "run_metadata"
TIMESTEP_EVENT_TYPE = "timestep"
POLICY_METRICS_EVENT_TYPE = "policy_metrics"


@dataclass(frozen=True)
class RunProvenance:
    schema_version: str
    run_id: str
    scenario_id: str
    seed: int
    horizon: int
    config_hash: str
    commit_hash: str
    timestamp_utc: str


@dataclass(frozen=True)
class EventEnvelope:
    schema_version: str
    event_type: str
    provenance: RunProvenance
    payload: Mapping[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class StateDiffRecord:
    changed_nodes: tuple[Mapping[str, Any], ...]
    added_edges: tuple[tuple[str, str], ...]
    removed_edges: tuple[tuple[str, str], ...]


@dataclass(frozen=True)
class ActionDecisionRecord:
    actor: str
    action_type: str
    targets: tuple[str, ...]
    rationale: str
    rationale_payload: Mapping[str, Any]
    changed: bool
    reason: str


@dataclass(frozen=True)
class MetricDeltaRecord:
    compromised_nodes_before: int
    compromised_nodes_after: int
    compromised_nodes_delta: int
    policy_metrics: Mapping[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class ReplayFrame:
    timestep: int
    pre_state_ref: str
    post_state_ref: str
    red_action: ActionDecisionRecord
    blue_action: ActionDecisionRecord
    state_diff: StateDiffRecord
    metric_delta: MetricDeltaRecord


@dataclass(frozen=True)
class ExperimentSummary:
    scenario_id: str
    report_file: str
    generated_at_utc: str
    metric_names: tuple[str, ...]