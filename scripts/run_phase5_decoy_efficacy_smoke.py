from __future__ import annotations

import json

from experiments.phase5_decoy_efficacy import run_phase5_decoy_efficacy


def main() -> None:
    output = run_phase5_decoy_efficacy(
        scenario_path="scenarios/library/phase5_branching_observability_v1.json",
        seeds=[20260329, 20260330],
        horizon=6,
        planner_depth=3,
    )
    print(json.dumps(output, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
