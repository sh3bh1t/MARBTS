from __future__ import annotations

from pathlib import Path
import tempfile

from experiments.phase2_comparison import run_phase2_multi_seed_report


def test_multi_seed_report_generates_expected_artifacts() -> None:
    with tempfile.TemporaryDirectory() as temp_dir:
        root = Path(temp_dir)
        output = run_phase2_multi_seed_report(
            scenario_path="scenarios/baselines/phase2_rule_baseline.json",
            seeds=[20260329, 20260330],
            horizon=6,
            runs_root=root / "runs",
            metrics_root=root / "metrics",
            reports_root=root / "reports",
        )

        report_file = Path(output["report_file"])
        report_payload = output["report"]

        assert report_file.exists()
        assert report_payload["aggregate"]["seed_count"] == 2
        assert report_payload["aggregate"]["scenario_id"] == "phase2-rule-baseline"
        assert report_payload["aggregate"]["horizon"] == 6
        assert "final_compromised_stddev" in report_payload["aggregate"]
        assert "blue_containment_stddev" in report_payload["aggregate"]
        assert "hash_frequency" in report_payload["aggregate"]
        assert "deterministic_consistency_ratio" in report_payload["aggregate"]
        assert 0.0 <= report_payload["aggregate"]["deterministic_consistency_ratio"] <= 1.0
        assert len(report_payload["runs"]) == 2

        for run in report_payload["runs"]:
            assert Path(run["run_dir"]).exists()
            assert Path(run["baseline_metrics_file"]).exists()
            assert run["sequence_hash"]