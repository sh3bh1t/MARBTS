from __future__ import annotations

from dataclasses import asdict
from typing import Any

from hart.models import (
    OBSERVABILITY_SCHEMA_VERSION,
    POLICY_METRICS_EVENT_TYPE,
    RUN_METADATA_EVENT_TYPE,
    TIMESTEP_EVENT_TYPE,
    RunMetadata,
    RunProvenance,
    SimulationRunResult,
    TimestepLogEntry,
)
from simulation.policy_trace import action_sequence_hash, summarize_action_counts, summarize_policy_metrics

from .provenance import collect_run_provenance
from .validation import validate_event_payload


def serialize_run_metadata(
    metadata: RunMetadata,
    *,
    final_state_ref: str,
    timesteps_count: int,
    provenance: RunProvenance | None = None,
) -> dict[str, Any]:
    resolved_provenance = provenance or collect_run_provenance(metadata)
    payload = asdict(metadata)
    payload.update(
        {
            "schema_version": OBSERVABILITY_SCHEMA_VERSION,
            "event_type": RUN_METADATA_EVENT_TYPE,
            "provenance": asdict(resolved_provenance),
            "final_state_ref": final_state_ref,
            "timesteps_count": timesteps_count,
        }
    )
    validate_event_payload(payload)
    return payload


def serialize_timestep_event(
    timestep: TimestepLogEntry,
    *,
    provenance: RunProvenance,
) -> dict[str, Any]:
    payload = asdict(timestep)
    payload.update(
        {
            "schema_version": OBSERVABILITY_SCHEMA_VERSION,
            "event_type": TIMESTEP_EVENT_TYPE,
            "provenance": asdict(provenance),
        }
    )
    validate_event_payload(payload)
    return payload


def serialize_policy_metrics_artifact(
    result: SimulationRunResult,
    *,
    provenance: RunProvenance,
) -> dict[str, Any]:
    payload = {
        "run_id": result.metadata.run_id,
        "scenario_id": result.metadata.scenario_id,
        "seed": result.metadata.seed,
        "horizon": result.metadata.horizon,
        "sequence_hash": action_sequence_hash(result),
        "action_counts": summarize_action_counts(result),
        "policy_metrics": summarize_policy_metrics(result),
        "schema_version": OBSERVABILITY_SCHEMA_VERSION,
        "event_type": POLICY_METRICS_EVENT_TYPE,
        "provenance": asdict(provenance),
    }
    validate_event_payload(payload)
    return payload