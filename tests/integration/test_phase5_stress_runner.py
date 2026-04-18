from pathlib import Path
import tempfile

from experiments.phase5_stress import run_phase5_stress_suite


def test_phase5_stress_suite_generates_summary_and_reports() -> None:
    with tempfile.TemporaryDirectory() as temp_dir:
        output = run_phase5_stress_suite(
            catalog_path="scenarios/library/catalog.json",
            stress_config_path="configs/experiments/phase5_stress_matrix.json",
            runs_root=Path(temp_dir) / "runs",
            reports_root=Path(temp_dir) / "reports",
        )

        assert Path(output["summary_file"]).exists()
        summary = output["summary"]
        assert summary["catalog_entry_count"] >= 3
        assert summary["reports"]
        assert all(item["aggregate_count"] > 0 for item in summary["reports"])
