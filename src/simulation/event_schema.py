from __future__ import annotations

from dataclasses import asdict

from hart.models import EventEnvelope, RunMetadata, RunProvenance, TimestepLogEntry


EVENT_SCHEMA_VERSION = "1.0.0"

_REQUIRED_TIMESTEP_PAYLOAD_FIELDS = {
    "timestep",
    "pre_state_ref",
    "post_state_ref",
    "red_action_intent",
    "blue_action_intent",
    "action_outcomes",
    "post_state_diff",
    "metric_delta",
}


def build_timestep_event(metadata: RunMetadata, timestep_entry: TimestepLogEntry) -> EventEnvelope:
    provenance = RunProvenance(
        run_id=metadata.run_id,
        seed=metadata.seed,
        scenario_id=metadata.scenario_id,
        scenario_version=metadata.scenario_version,
        horizon=metadata.horizon,
        config_hash=metadata.config_hash,
        commit_hash=metadata.commit_hash,
        code_version=metadata.code_version,
        timestamp_utc=metadata.timestamp_utc,
    )

    return EventEnvelope(
        schema_version=EVENT_SCHEMA_VERSION,
        event_type="timestep",
        event_id=f"{metadata.run_id}:timestep:{timestep_entry.timestep}",
        provenance=provenance,
        payload=asdict(timestep_entry),
    )


def validate_event_envelope(event: dict) -> None:
    required_top_level = {"schema_version", "event_type", "event_id", "provenance", "payload"}
    missing_top_level = required_top_level.difference(event.keys())
    if missing_top_level:
        missing = ", ".join(sorted(missing_top_level))
        raise ValueError(f"event envelope missing required fields: {missing}")

    provenance = event["provenance"]
    if not isinstance(provenance, dict):
        raise ValueError("event provenance must be an object")

    required_provenance_fields = {
        "run_id",
        "seed",
        "scenario_id",
        "scenario_version",
        "horizon",
        "config_hash",
        "commit_hash",
        "code_version",
        "timestamp_utc",
    }
    missing_provenance = required_provenance_fields.difference(provenance.keys())
    if missing_provenance:
        missing = ", ".join(sorted(missing_provenance))
        raise ValueError(f"event provenance missing required fields: {missing}")

    payload = event["payload"]
    if not isinstance(payload, dict):
        raise ValueError("event payload must be an object")

    missing_payload = _REQUIRED_TIMESTEP_PAYLOAD_FIELDS.difference(payload.keys())
    if missing_payload:
        missing = ", ".join(sorted(missing_payload))
        raise ValueError(f"timestep payload missing required fields: {missing}")
