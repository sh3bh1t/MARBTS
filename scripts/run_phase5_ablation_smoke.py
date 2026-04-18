from __future__ import annotations

import json

from experiments.phase5_ablation_suite import run_phase5_ablation_suite
from experiments.scenario_catalog import resolve_catalog_scenario_path


def main() -> None:
    catalog_path = "scenarios/library/catalog.json"
    matrix_path = "configs/experiments/phase5_ablation_matrix.json"
    scenario_path = resolve_catalog_scenario_path(catalog_path, "phase5-branching-observability")
    output = run_phase5_ablation_suite(
        matrix_path=matrix_path,
        scenario_path=scenario_path,
        catalog_path=catalog_path,
    )
    print(
        json.dumps(
            {
                "report_file": output["report_file"],
                "publication_table_file": output["publication_table_file"],
                "summary_file": output["summary_file"],
                "manifest_file": output["manifest_file"],
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
