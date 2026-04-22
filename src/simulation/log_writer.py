from __future__ import annotations

import json
from pathlib import Path

from observability import collect_run_provenance, serialize_policy_metrics_artifact, serialize_run_metadata, serialize_timestep_event
from simulation.kernel import SimulationRunResult
from simulation.state_diff import snapshot_ref


def write_run_artifacts(result: SimulationRunResult, output_root: str | Path) -> dict[str, str]:
    root = Path(output_root)
    run_dir = root / result.metadata.run_id
    run_dir.mkdir(parents=True, exist_ok=True)

    metadata_path = run_dir / "run_metadata.json"
    timesteps_path = run_dir / "timesteps.jsonl"
    policy_metrics_path = run_dir / "policy_metrics.json"

    provenance = collect_run_provenance(result.metadata)
    metadata_payload = serialize_run_metadata(
        result.metadata,
        final_state_ref=snapshot_ref(result.final_graph),
        timesteps_count=len(result.timesteps),
        provenance=provenance,
    )

    with metadata_path.open("w", encoding="utf-8") as metadata_file:
        json.dump(metadata_payload, metadata_file, indent=2, sort_keys=True)

    with timesteps_path.open("w", encoding="utf-8") as timesteps_file:
        for timestep in result.timesteps:
            timesteps_file.write(json.dumps(serialize_timestep_event(timestep, provenance=provenance), sort_keys=True))
            timesteps_file.write("\n")

    policy_metrics_payload = serialize_policy_metrics_artifact(result, provenance=provenance)
    with policy_metrics_path.open("w", encoding="utf-8") as policy_metrics_file:
        json.dump(policy_metrics_payload, policy_metrics_file, indent=2, sort_keys=True)

    return {
        "run_dir": str(run_dir),
        "metadata_file": str(metadata_path),
        "timesteps_file": str(timesteps_path),
        "policy_metrics_file": str(policy_metrics_path),
    }
