from __future__ import annotations

from pathlib import Path
import tempfile

from experiments.policy_experiment_matrix import run_policy_experiment_matrix


def test_policy_experiment_matrix_generates_condition_aggregates_and_artifacts() -> None:
    with tempfile.TemporaryDirectory() as temp_dir:
        root = Path(temp_dir)
        output = run_policy_experiment_matrix(
            scenario_path="scenarios/baselines/rule_baseline.json",
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
        assert report["matrix_metadata"]["seed_count"] == 2
        assert report["matrix_metadata"]["horizon"] == 2
        assert report["matrix_metadata"]["include_ablations"] is True
        assert report["matrix_metadata"]["condition_count"] == 6

        condition_ids = {aggregate["condition_id"] for aggregate in report["condition_aggregates"]}
        assert "rule_red_vs_rule_blue" in condition_ids
        assert "adaptive_red_vs_rule_blue" in condition_ids
        assert "rule_red_vs_adaptive_blue" in condition_ids
        assert "adaptive_red_vs_adaptive_blue" in condition_ids
        assert "adaptive_red_no_planning_vs_rule_blue" in condition_ids
        assert "adaptive_red_reduced_observability_vs_rule_blue" in condition_ids

        assert any(
            aggregate["ablation"]["no_planning"]
            for aggregate in report["condition_aggregates"]
        )
        assert any(
            aggregate["ablation"]["reduced_observability"]
            for aggregate in report["condition_aggregates"]
        )

        assert len(report["comparison_to_baseline"]) == 6
        assert len(report["runs"]) == 12

        for run in report["runs"]:
            assert Path(run["run_dir"]).exists()
            assert Path(run["baseline_metrics_file"]).exists()
            assert run["sequence_hash"]