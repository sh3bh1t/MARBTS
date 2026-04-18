from __future__ import annotations

import json

from experiments.phase5_stress import run_phase5_stress_suite


def main() -> None:
    output = run_phase5_stress_suite(
        catalog_path="scenarios/library/catalog.json",
        stress_config_path="configs/experiments/phase5_stress_matrix.json",
    )
    print(json.dumps(output, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
