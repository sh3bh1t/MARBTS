from __future__ import annotations

from typing import Any, Mapping

from hart.models import (
    OBSERVABILITY_SCHEMA_VERSION,
    POLICY_METRICS_EVENT_TYPE,
    RUN_METADATA_EVENT_TYPE,
    TIMESTEP_EVENT_TYPE,
)


_BASE_REQUIRED_FIELDS = {"schema_version", "event_type", "provenance"}
_PROVENANCE_REQUIRED_FIELDS = {
    "schema_version",
    "run_id",
    "scenario_id",
    "seed",
    "horizon",
    "config_hash",
    "commit_hash",
    "timestamp_utc",
}
_EVENT_REQUIRED_FIELDS = {
    RUN_METADATA_EVENT_TYPE: {"run_id", "seed", "scenario_id", "horizon", "timestamp_utc", "final_state_ref", "timesteps_count"},
    TIMESTEP_EVENT_TYPE: {
        "timestep",
        "pre_state_ref",
        "post_state_ref",
        "red_action_intent",
        "blue_action_intent",
        "action_outcomes",
        "post_state_diff",
        "metric_delta",
    },
    POLICY_METRICS_EVENT_TYPE: {
        "run_id",
        "scenario_id",
        "seed",
        "horizon",
        "sequence_hash",
        "action_counts",
        "policy_metrics",
    },
}


def _assert_required_fields(payload: Mapping[str, Any], required_fields: set[str], *, label: str) -> None:
    missing = sorted(required_fields - set(payload.keys()))
    if missing:
        raise ValueError(f"{label} missing required fields: {', '.join(missing)}")


def validate_event_payload(payload: Mapping[str, Any]) -> None:
    _assert_required_fields(payload, _BASE_REQUIRED_FIELDS, label="event envelope")
    if payload["schema_version"] != OBSERVABILITY_SCHEMA_VERSION:
        raise ValueError("event envelope has unsupported schema version")

    provenance = payload["provenance"]
    if not isinstance(provenance, Mapping):
        raise ValueError("event envelope provenance must be a mapping")
    _assert_required_fields(provenance, _PROVENANCE_REQUIRED_FIELDS, label="event provenance")
    if provenance["schema_version"] != OBSERVABILITY_SCHEMA_VERSION:
        raise ValueError("event provenance has unsupported schema version")

    event_type = payload["event_type"]
    event_required_fields = _EVENT_REQUIRED_FIELDS.get(event_type)
    if event_required_fields is None:
        raise ValueError(f"unsupported event_type: {event_type}")
    _assert_required_fields(payload, _BASE_REQUIRED_FIELDS | event_required_fields, label=f"{event_type} event")