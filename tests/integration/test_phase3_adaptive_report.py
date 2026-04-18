from pathlib import Path
import tempfile

from experiments.phase3_adaptive_comparison import run_phase3_adaptive_comparison
from visualization.reporting import write_phase3_markdown_summary


def test_phase3_adaptive_report_and_markdown_summary() -> None:
    with tempfile.TemporaryDirectory() as temp_dir:
        output = run_phase3_adaptive_comparison(
            scenario_path="scenarios/baselines/phase2_rule_baseline.json",
            seeds=[20260329],
            horizon=4,
            runs_root=Path(temp_dir) / "runs",
            reports_root=Path(temp_dir) / "reports",
        )

        report = output["report"]
        assert Path(output["report_file"]).exists()
        assert report["aggregates"]
        assert any(item["condition_id"] == "adaptive_blue_ablation_depth1" for item in report["aggregates"])

        summary_path = write_phase3_markdown_summary(report, Path(temp_dir) / "reports" / "phase3.md")
        summary_text = Path(summary_path).read_text(encoding="utf-8")
        assert "Phase 3 Adaptive Comparison" in summary_text
        assert "adaptive_blue_ablation_depth1" in summary_text
