from __future__ import annotations

from dataclasses import asdict
import hashlib
import json
from pathlib import Path
from typing import Any, Mapping

from hart.models import ActionDecisionRecord, MetricDeltaRecord, ReplayFrame, StateDiffRecord

from .validation import validate_event_payload


def _load_json_payload(file_path: str | Path) -> dict[str, Any]:
    path = Path(file_path)
    return json.loads(path.read_text(encoding="utf-8"))


def _load_json_lines(file_path: str | Path) -> tuple[dict[str, Any], ...]:
    path = Path(file_path)
    payloads: list[dict[str, Any]] = []
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        if not raw_line.strip():
            continue
        payload = json.loads(raw_line)
        validate_event_payload(payload)
        payloads.append(payload)
    return tuple(payloads)


def _coerce_action_decision(payload: Mapping[str, Any]) -> ActionDecisionRecord:
    return ActionDecisionRecord(
        actor=str(payload["actor"]),
        action_type=str(payload["action_type"]),
        targets=tuple(str(target) for target in payload.get("targets", ())),
        rationale=str(payload["rationale"]),
        rationale_payload=dict(payload.get("rationale_payload", {})),
        changed=bool(payload["changed"]),
        reason=str(payload["reason"]),
    )


def _coerce_state_diff(payload: Mapping[str, Any]) -> StateDiffRecord:
    return StateDiffRecord(
        changed_nodes=tuple(dict(node) for node in payload.get("changed_nodes", ())),
        added_edges=tuple(tuple(edge) for edge in payload.get("added_edges", ())),
        removed_edges=tuple(tuple(edge) for edge in payload.get("removed_edges", ())),
    )


def _coerce_metric_delta(payload: Mapping[str, Any]) -> MetricDeltaRecord:
    return MetricDeltaRecord(
        compromised_nodes_before=int(payload.get("compromised_nodes_before", 0)),
        compromised_nodes_after=int(payload.get("compromised_nodes_after", 0)),
        compromised_nodes_delta=int(payload.get("compromised_nodes_delta", 0)),
        policy_metrics=dict(payload.get("policy_metrics", {})),
    )


def _action_sequence_hash_from_frames(frames: tuple[ReplayFrame, ...]) -> str:
    trace_payload = [
        {
            "timestep": frame.timestep,
            "red_action": frame.red_action.action_type,
            "red_targets": list(frame.red_action.targets),
            "blue_action": frame.blue_action.action_type,
            "blue_targets": list(frame.blue_action.targets),
        }
        for frame in frames
    ]
    payload = json.dumps(trace_payload, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def load_replay_frames(timesteps_file: str | Path) -> tuple[ReplayFrame, ...]:
    frames: list[ReplayFrame] = []
    for payload in _load_json_lines(timesteps_file):
        frames.append(
            ReplayFrame(
                timestep=int(payload["timestep"]),
                pre_state_ref=str(payload["pre_state_ref"]),
                post_state_ref=str(payload.get("post_state_ref", "")),
                red_action=_coerce_action_decision(payload["red_action_intent"]),
                blue_action=_coerce_action_decision(payload["blue_action_intent"]),
                state_diff=_coerce_state_diff(payload["post_state_diff"]),
                metric_delta=_coerce_metric_delta(payload["metric_delta"]),
            )
        )
    return tuple(frames)


def summarize_replay_frames(frames: tuple[ReplayFrame, ...]) -> dict[str, Any]:
    if not frames:
        return {
            "timesteps_count": 0,
            "final_compromised_nodes": 0,
            "blue_containment_actions": 0,
            "first_containment_timestep": -1,
            "sequence_hash": "",
        }

    blue_containment_actions = sum(1 for frame in frames if frame.blue_action.action_type in {"block", "isolate"})
    first_containment_timestep = -1
    for frame in frames:
        if frame.blue_action.action_type in {"block", "isolate"}:
            first_containment_timestep = frame.timestep
            break

    final_frame = frames[-1]
    return {
        "timesteps_count": len(frames),
        "final_compromised_nodes": final_frame.metric_delta.compromised_nodes_after,
        "blue_containment_actions": blue_containment_actions,
        "first_containment_timestep": first_containment_timestep,
        "sequence_hash": _action_sequence_hash_from_frames(frames),
    }


def load_run_artifact_bundle(run_dir: str | Path) -> dict[str, Any]:
    root = Path(run_dir)
    metadata_path = root / "run_metadata.json"
    timesteps_path = root / "timesteps.jsonl"
    policy_metrics_path = root / "policy_metrics.json"

    metadata = _load_json_payload(metadata_path)
    policy_metrics = _load_json_payload(policy_metrics_path)
    validate_event_payload(metadata)
    validate_event_payload(policy_metrics)

    frames = load_replay_frames(timesteps_path)
    replay_summary = summarize_replay_frames(frames)
    sequence_hash_matches = policy_metrics.get("sequence_hash") == replay_summary["sequence_hash"]

    summary = {
        "run_id": metadata["run_id"],
        "scenario_id": metadata["scenario_id"],
        "seed": metadata["seed"],
        "horizon": metadata["horizon"],
        "timesteps_count": replay_summary["timesteps_count"],
        "timestamp_utc": metadata["timestamp_utc"],
        "final_state_ref": metadata["final_state_ref"],
        "sequence_hash": policy_metrics["sequence_hash"],
        "replay_sequence_hash": replay_summary["sequence_hash"],
        "sequence_hash_matches": sequence_hash_matches,
        "final_compromised_nodes": replay_summary["final_compromised_nodes"],
        "blue_containment_actions": replay_summary["blue_containment_actions"],
        "first_containment_timestep": replay_summary["first_containment_timestep"],
        "action_counts": policy_metrics["action_counts"],
        "policy_metrics": policy_metrics["policy_metrics"],
        "provenance": metadata["provenance"],
    }

    return {
        "metadata": metadata,
        "policy_metrics": policy_metrics,
        "frames": frames,
        "replay_summary": replay_summary,
        "summary": summary,
    }