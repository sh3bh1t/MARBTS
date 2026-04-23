from __future__ import annotations

from pathlib import Path
import tempfile

from experiments.stress_test_suite import run_stress_test_suite
from hart.models import StressTestConfig


def test_stress_test_suite_generates_ranked_profile_report_and_observability_penalty() -> None:
    with tempfile.TemporaryDirectory() as temp_dir:
        root = Path(temp_dir)
        profiles = (
            StressTestConfig(
                profile_id="scale-smoke",
                label="Scale Smoke",
                scenario_paths=("scenarios/library/scale_chain_6.json",),
                seeds=(20260423,),
                horizon=2,
                include_ablations=False,
            ),
            StressTestConfig(
                profile_id="noise-smoke",
                label="Noise/Observability Smoke",
                scenario_paths=("scenarios/library/containment_stress.json",),
                seeds=(20260424,),
                horizon=2,
                include_ablations=True,
                observation_noise_proxy=True,
            ),
        )

        output = run_stress_test_suite(
            profiles=profiles,
            runs_root=root / "runs",
            metrics_root=root / "metrics",
            reports_root=root / "reports",
        )

        report_file = Path(output["report_file"])
        report = output["report"]

        assert report_file.exists()
        assert report["suite_metadata"]["profile_count"] == 2
        assert set(report["suite_metadata"]["profiles"]) == {"scale-smoke", "noise-smoke"}

        profile_reports = report["profile_reports"]
        assert len(profile_reports) == 2
        assert len(report["profile_rankings"]["lowest_baseline_compromised"]) == 2

        summaries = {item["summary"]["profile_id"]: item["summary"] for item in profile_reports}
        assert summaries["scale-smoke"]["include_ablations"] is False
        assert summaries["noise-smoke"]["include_ablations"] is True
        assert summaries["noise-smoke"]["observation_noise_proxy"] is True

        observability_penalty = summaries["noise-smoke"].get("observability_penalty")
        assert observability_penalty is not None
        assert observability_penalty["sample_count"] >= 1
        assert observability_penalty["combined_penalty_mean"] is not None

        for profile_report in profile_reports:
            assert Path(profile_report["report_file"]).exists()
            assert "scenario_reports" in profile_report["report"]
