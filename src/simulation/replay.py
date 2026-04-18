from __future__ import annotations

from hart.models import ReplayFrame
from simulation.graph_codec import graph_from_snapshot_payload
from simulation.state_diff import snapshot_ref


def _copy_snapshot(snapshot: dict) -> dict:
    return {
        "nodes": {node_id: dict(node_state) for node_id, node_state in snapshot["nodes"].items()},
        "edges": [tuple(edge) for edge in snapshot["edges"]],
    }


def _apply_state_diff(snapshot: dict, state_diff: dict) -> dict:
    next_snapshot = _copy_snapshot(snapshot)

    for changed_node in state_diff.get("changed_nodes", []):
        next_snapshot["nodes"][changed_node["node_id"]] = dict(changed_node["after"])

    edge_set = {tuple(edge) for edge in next_snapshot["edges"]}
    for edge in state_diff.get("removed_edges", []):
        edge_set.discard(tuple(edge))
    for edge in state_diff.get("added_edges", []):
        edge_set.add(tuple(edge))
    next_snapshot["edges"] = sorted(edge_set)
    return next_snapshot


def replay_from_initial_snapshot(initial_snapshot: dict, timestep_payloads: list[dict]) -> tuple[ReplayFrame, ...]:
    current_snapshot = _copy_snapshot(initial_snapshot)
    frames = [
        ReplayFrame(
            timestep=-1,
            state_ref=snapshot_ref(graph_from_snapshot_payload(current_snapshot)),
            state_snapshot=_copy_snapshot(current_snapshot),
        )
    ]

    for timestep_payload in timestep_payloads:
        current_snapshot = _apply_state_diff(current_snapshot, timestep_payload["post_state_diff"])
        frames.append(
            ReplayFrame(
                timestep=int(timestep_payload["timestep"]),
                state_ref=snapshot_ref(graph_from_snapshot_payload(current_snapshot)),
                state_snapshot=_copy_snapshot(current_snapshot),
            )
        )

    return tuple(frames)
