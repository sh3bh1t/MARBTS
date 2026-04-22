from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

from environment.graph_builder import build_graph_from_scenario
from schemas.scenario import load_scenario_file
from simulation.kernel import run_turn_based_simulation
from simulation.log_writer import write_run_artifacts


def main() -> None:
    scenario_path = Path("scenarios/baselines/minimal_valid.json")
    scenario = load_scenario_file(scenario_path)
    graph = build_graph_from_scenario(scenario)

    seed = 20260328
    horizon = 5
    result = run_turn_based_simulation(
        graph,
        seed=seed,
        horizon=horizon,
        scenario_id=scenario.metadata.scenario_id,
    )

    artifacts_root = Path("artifacts/runs")
    output_paths = write_run_artifacts(result, artifacts_root)

    print("NETWORK_CORE_SMOKE_OK")
    print(f"timestamp_utc={datetime.now(timezone.utc).isoformat()}")
    print(f"scenario_id={scenario.metadata.scenario_id}")
    print(f"seed={seed}")
    print(f"horizon={horizon}")
    print(f"run_id={result.metadata.run_id}")
    print(f"run_dir={output_paths['run_dir']}")
    print(f"metadata_file={output_paths['metadata_file']}")
    print(f"timesteps_file={output_paths['timesteps_file']}")


if __name__ == "__main__":
    main()
