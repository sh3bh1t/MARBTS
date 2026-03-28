from __future__ import annotations

import hashlib
import json

from hart.models import SimulationRunResult


def action_sequence_hash(result: SimulationRunResult) -> str:
    trace_payload = [
        {
            "timestep": entry.timestep,
            "red_action": entry.red_action_intent.action_type,
            "red_targets": list(entry.red_action_intent.targets),
            "blue_action": entry.blue_action_intent.action_type,
            "blue_targets": list(entry.blue_action_intent.targets),
        }
        for entry in result.timesteps
    ]

    payload = json.dumps(trace_payload, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def summarize_action_counts(result: SimulationRunResult) -> dict[str, dict[str, int]]:
    summary: dict[str, dict[str, int]] = {"red": {}, "blue": {}}

    for entry in result.timesteps:
        red_type = entry.red_action_intent.action_type
        blue_type = entry.blue_action_intent.action_type
        summary["red"][red_type] = summary["red"].get(red_type, 0) + 1
        summary["blue"][blue_type] = summary["blue"].get(blue_type, 0) + 1

    return summary


def summarize_policy_metrics(result: SimulationRunResult) -> dict[str, dict]:
    latest: dict[str, dict] = {}
    for entry in result.timesteps:
        policy_metrics = entry.metric_delta.get("policy_metrics", {})
        for actor, snapshot in policy_metrics.items():
            latest[actor] = snapshot
    return latest