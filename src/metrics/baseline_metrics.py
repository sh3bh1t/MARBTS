from __future__ import annotations

import json
from pathlib import Path

from hart.models import SimulationRunResult
from simulation.policy_trace import action_sequence_hash


def _mean(values: list[float]) -> float:
    if not values:
        return 0.0
    return sum(values) / len(values)


def compute_baseline_metrics(result: SimulationRunResult) -> dict:
    compromised_before = [
        float(entry.metric_delta.get("compromised_nodes_before", 0))
        for entry in result.timesteps
    ]
    compromised_after = [
        float(entry.metric_delta.get("compromised_nodes_after", 0))
        for entry in result.timesteps
    ]

    red_changed = sum(1 for entry in result.timesteps if entry.red_action_intent.changed)
    blue_changed = sum(1 for entry in result.timesteps if entry.blue_action_intent.changed)

    blue_containment_actions = sum(
        1
        for entry in result.timesteps
        if entry.blue_action_intent.action_type in {"block", "isolate"}
    )
    red_offensive_actions = sum(
        1
        for entry in result.timesteps
        if entry.red_action_intent.action_type in {"scan", "exploit", "lateral_move", "escalate"}
    )

    first_containment_timestep = -1
    for entry in result.timesteps:
        if entry.blue_action_intent.action_type in {"block", "isolate"}:
            first_containment_timestep = entry.timestep
            break

    timesteps_count = len(result.timesteps)
    final_compromised = int(compromised_after[-1]) if compromised_after else 0
    initial_compromised = int(compromised_before[0]) if compromised_before else 0

    return {
        "run_id": result.metadata.run_id,
        "scenario_id": result.metadata.scenario_id,
        "seed": result.metadata.seed,
        "horizon": result.metadata.horizon,
        "timesteps_count": timesteps_count,
        "sequence_hash": action_sequence_hash(result),
        "security_outcomes": {
            "initial_compromised_nodes": initial_compromised,
            "final_compromised_nodes": final_compromised,
            "max_compromised_nodes": int(max(compromised_after)) if compromised_after else 0,
            "compromise_delta": final_compromised - initial_compromised,
            "mean_compromised_nodes": round(_mean(compromised_after), 3),
        },
        "policy_performance": {
            "red_changed_actions": red_changed,
            "blue_changed_actions": blue_changed,
            "red_action_change_rate": round(red_changed / timesteps_count, 3) if timesteps_count else 0.0,
            "blue_action_change_rate": round(blue_changed / timesteps_count, 3) if timesteps_count else 0.0,
            "red_offensive_actions": red_offensive_actions,
            "blue_containment_actions": blue_containment_actions,
            "first_containment_timestep": first_containment_timestep,
        },
    }


def write_baseline_metrics_artifact(
    result: SimulationRunResult,
    output_root: str | Path,
) -> str:
    root = Path(output_root)
    root.mkdir(parents=True, exist_ok=True)

    output_path = root / f"{result.metadata.run_id}.json"
    payload = compute_baseline_metrics(result)

    output_path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
    return str(output_path)