from pathlib import Path
import tempfile

from experiments.phase5_ablation_suite import run_phase5_ablation_suite
from experiments.scenario_catalog import resolve_catalog_scenario_path


def test_phase5_ablation_suite_generates_bundle() -> None:
    with tempfile.TemporaryDirectory() as temp_dir:
        catalog_path = "scenarios/library/catalog.json"
        scenario_path = resolve_catalog_scenario_path(catalog_path, "phase5-branching-observability")
        output = run_phase5_ablation_suite(
            matrix_path="configs/experiments/phase5_ablation_matrix.json",
            scenario_path=scenario_path,
            catalog_path=catalog_path,
            runs_root=Path(temp_dir) / "runs",
            reports_root=Path(temp_dir) / "reports",
        )

        assert Path(output["report_file"]).exists()
        assert Path(output["publication_table_file"]).exists()
        assert Path(output["summary_file"]).exists()
        assert Path(output["manifest_file"]).exists()
        assert any(item["condition_id"] == "adaptive_blue_prefer_feint" for item in output["report"]["aggregates"])
