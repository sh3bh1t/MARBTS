from pathlib import Path
import tempfile

from experiments.phase5_decoy_efficacy import run_phase5_decoy_efficacy


def test_phase5_decoy_efficacy_generates_report() -> None:
    with tempfile.TemporaryDirectory() as temp_dir:
        output = run_phase5_decoy_efficacy(
            scenario_path="scenarios/library/phase5_branching_observability_v1.json",
            seeds=[20260329],
            horizon=4,
            planner_depth=2,
            runs_root=Path(temp_dir) / "runs",
            reports_root=Path(temp_dir) / "reports",
        )

        assert Path(output["report_file"]).exists()
        report = output["report"]
        assert report["efficacy_summary"]
        assert "efficacy_observed" in report["efficacy_summary"]
        assert any(item["condition_id"] == "adaptive_blue_with_decoy" for item in report["aggregates"])
        assert any(item["condition_id"] == "adaptive_blue_without_decoy" for item in report["aggregates"])
        assert any(item["red_mode"] == "aggressive" for item in report["aggregates"])
