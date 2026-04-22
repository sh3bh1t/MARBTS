from __future__ import annotations

from pathlib import Path
import tempfile

from experiments.policy_experiment_matrix import run_policy_experiment_matrix_batch


def test_policy_experiment_matrix_batch_generates_ranked_scenario_reports() -> None:
    with tempfile.TemporaryDirectory() as temp_dir:
        root = Path(temp_dir)
        output = run_policy_experiment_matrix_batch(
            scenario_paths=[
                "scenarios/baselines/rule_baseline.json",
                "scenarios/library/containment_stress.json",
            ],
            seeds=[20260423, 20260424],
            horizon=2,
            runs_root=root / "runs",
            metrics_root=root / "metrics",
            reports_root=root / "reports",
            include_ablations=True,
        )

        report_file = Path(output["report_file"])
        report = output["report"]

        assert report_file.exists()
        assert report["batch_metadata"]["scenario_count"] == 2
        assert report["batch_metadata"]["seed_count"] == 2
        assert len(report["scenario_reports"]) == 2
        assert len(report["scenario_rankings"]["lowest_baseline_compromised"]) == 2

        scenario_ids = {scenario_report["report"]["matrix_metadata"]["scenario_id"] for scenario_report in report["scenario_reports"]}
        assert scenario_ids == {"rule-baseline", "containment-stress"}

        for scenario_report in report["scenario_reports"]:
            assert Path(scenario_report["report_file"]).exists()
            assert "summary_rankings" in scenario_report["report"]