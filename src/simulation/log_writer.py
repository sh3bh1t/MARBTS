from __future__ import annotations

from dataclasses import asdict
import json
from pathlib import Path

from simulation.kernel import SimulationRunResult
from simulation.state_diff import snapshot_ref


def write_run_artifacts(result: SimulationRunResult, output_root: str | Path) -> dict[str, str]:
    root = Path(output_root)
    run_dir = root / result.metadata.run_id
    run_dir.mkdir(parents=True, exist_ok=True)

    metadata_path = run_dir / "run_metadata.json"
    timesteps_path = run_dir / "timesteps.jsonl"

    metadata_payload = asdict(result.metadata)
    metadata_payload["final_state_ref"] = snapshot_ref(result.final_graph)
    metadata_payload["timesteps_count"] = len(result.timesteps)

    with metadata_path.open("w", encoding="utf-8") as metadata_file:
        json.dump(metadata_payload, metadata_file, indent=2, sort_keys=True)

    with timesteps_path.open("w", encoding="utf-8") as timesteps_file:
        for timestep in result.timesteps:
            timesteps_file.write(json.dumps(asdict(timestep), sort_keys=True))
            timesteps_file.write("\n")

    return {
        "run_dir": str(run_dir),
        "metadata_file": str(metadata_path),
        "timesteps_file": str(timesteps_path),
    }
