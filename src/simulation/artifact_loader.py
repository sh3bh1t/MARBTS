from __future__ import annotations

import json
from pathlib import Path

from simulation.event_schema import validate_event_envelope
from simulation.replay import replay_from_initial_snapshot
from simulation.state_diff import snapshot_ref


def _read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _read_jsonl(path: Path) -> list[dict]:
    lines = [line for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
    return [json.loads(line) for line in lines]


def load_run_artifacts(run_dir: str | Path) -> dict[str, object]:
    root = Path(run_dir)
    metadata = _read_json(root / "run_metadata.json")
    initial_state = _read_json(root / "initial_state.json")
    final_state = _read_json(root / "final_state.json")
    timesteps = _read_jsonl(root / "timesteps.jsonl")
    events = _read_jsonl(root / "events.jsonl")
    policy_metrics = _read_json(root / "policy_metrics.json")

    return {
        "run_dir": str(root),
        "metadata": metadata,
        "initial_state": initial_state,
        "final_state": final_state,
        "timesteps": timesteps,
        "events": events,
        "policy_metrics": policy_metrics,
    }


def load_comparison_report(report_file: str | Path) -> dict[str, object]:
    path = Path(report_file)
    return _read_json(path)


def validate_run_artifacts(run_artifacts: dict[str, object]) -> dict[str, object]:
    events = list(run_artifacts["events"])
    timesteps = list(run_artifacts["timesteps"])
    metadata = dict(run_artifacts["metadata"])
    final_state = dict(run_artifacts["final_state"])

    for event in events:
        validate_event_envelope(event)

    if len(events) != len(timesteps):
        raise ValueError("events.jsonl and timesteps.jsonl length mismatch")

    required_metadata_fields = {
        "run_id",
        "seed",
        "scenario_id",
        "scenario_version",
        "horizon",
        "config_hash",
        "commit_hash",
        "code_version",
        "timestamp_utc",
        "initial_state_ref",
        "final_state_ref",
    }
    missing_metadata = required_metadata_fields.difference(metadata.keys())
    if missing_metadata:
        missing = ", ".join(sorted(missing_metadata))
        raise ValueError(f"run metadata missing required fields: {missing}")

    final_state_ref = snapshot_ref_from_payload(final_state)
    if metadata["final_state_ref"] != final_state_ref:
        raise ValueError("final_state_ref does not match final_state.json payload")

    required_timestep_fields = {
        "timestep",
        "pre_state_ref",
        "post_state_ref",
        "red_action_intent",
        "blue_action_intent",
        "action_outcomes",
        "post_state_diff",
        "metric_delta",
    }
    completed_timesteps = 0
    missing_timestep_fields: list[dict[str, object]] = []
    for timestep in timesteps:
        missing = sorted(required_timestep_fields.difference(timestep.keys()))
        if missing:
            missing_timestep_fields.append({"timestep": timestep.get("timestep", "unknown"), "missing": missing})
            continue
        completed_timesteps += 1

    if missing_timestep_fields:
        raise ValueError(f"timesteps.jsonl missing required fields: {missing_timestep_fields}")

    event_mismatches: list[str] = []
    for index, event in enumerate(events):
        provenance = event["provenance"]
        payload = event["payload"]
        timestep = timesteps[index]
        if provenance["run_id"] != metadata["run_id"]:
            event_mismatches.append(f"event[{index}] run_id mismatch")
        if provenance["scenario_id"] != metadata["scenario_id"]:
            event_mismatches.append(f"event[{index}] scenario_id mismatch")
        if provenance["seed"] != metadata["seed"]:
            event_mismatches.append(f"event[{index}] seed mismatch")
        if provenance["horizon"] != metadata["horizon"]:
            event_mismatches.append(f"event[{index}] horizon mismatch")
        if payload["timestep"] != timestep["timestep"]:
            event_mismatches.append(f"event[{index}] timestep mismatch")
        if payload["pre_state_ref"] != timestep["pre_state_ref"]:
            event_mismatches.append(f"event[{index}] pre_state_ref mismatch")
        if payload["post_state_ref"] != timestep["post_state_ref"]:
            event_mismatches.append(f"event[{index}] post_state_ref mismatch")

    if event_mismatches:
        raise ValueError(f"event/timestep consistency failures: {event_mismatches}")

    action_types: dict[str, dict[str, int]] = {"red": {}, "blue": {}}
    max_compromised = 0
    timeline_rows: list[dict[str, object]] = []
    for timestep in timesteps:
        timeline_row = {
            "timestep": timestep["timestep"],
            "red_action": f"{timestep['red_action_intent']['action_type']} {list(timestep['red_action_intent']['targets'])}",
            "blue_action": f"{timestep['blue_action_intent']['action_type']} {list(timestep['blue_action_intent']['targets'])}",
            "compromised_after": int(timestep["metric_delta"]["compromised_nodes_after"]),
            "changed_nodes": len(timestep["post_state_diff"]["changed_nodes"]),
        }
        timeline_rows.append(timeline_row)
        for actor in ("red", "blue"):
            action_type = timestep[f"{actor}_action_intent"]["action_type"]
            action_types[actor][action_type] = action_types[actor].get(action_type, 0) + 1
        max_compromised = max(max_compromised, timeline_row["compromised_after"])

    return {
        "event_count": len(events),
        "timestep_count": len(timesteps),
        "log_completeness_ratio": round(completed_timesteps / len(timesteps), 3) if timesteps else 1.0,
        "final_state_ref": final_state_ref,
        "max_compromised_nodes": max_compromised,
        "action_type_counts": action_types,
        "timeline_rows": timeline_rows,
    }


def snapshot_ref_from_payload(payload: dict) -> str:
    from simulation.graph_codec import graph_from_snapshot_payload

    return snapshot_ref(graph_from_snapshot_payload(payload))


def reconstruct_run_replay(run_artifacts: dict[str, object]) -> tuple[dict, ...]:
    frames = replay_from_initial_snapshot(
        dict(run_artifacts["initial_state"]),
        list(run_artifacts["timesteps"]),
    )
    return tuple(
        {
            "timestep": frame.timestep,
            "state_ref": frame.state_ref,
            "state_snapshot": frame.state_snapshot,
        }
        for frame in frames
    )
