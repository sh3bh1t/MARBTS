from __future__ import annotations

from dataclasses import asdict
from datetime import datetime, timezone
import json
from pathlib import Path

from experiments.policy_experiment_matrix import run_policy_experiment_matrix_batch
from hart.models import StressTestConfig


def _mean(values: list[float]) -> float:
    if not values:
        return 0.0
    return sum(values) / len(values)


def _condition_metric(report: dict, condition_id: str, metric_name: str) -> float | None:
    for aggregate in report.get("condition_aggregates", []):
        if aggregate.get("condition_id") == condition_id:
            metric_bundle = aggregate.get("metric_bundle", {})
            if metric_name in metric_bundle:
                return float(metric_bundle[metric_name])
            return None
    return None


def _compute_observability_penalty(batch_report: dict) -> dict[str, float | int | None]:
    red_penalties: list[float] = []
    blue_penalties: list[float] = []

    for scenario_report in batch_report.get("scenario_reports", []):
        matrix_report = scenario_report.get("report", {})
        baseline = _condition_metric(matrix_report, "adaptive_red_vs_adaptive_blue", "final_compromised_mean")
        red_reduced = _condition_metric(
            matrix_report,
            "adaptive_red_reduced_observability_vs_adaptive_blue",
            "final_compromised_mean",
        )
        blue_reduced = _condition_metric(
            matrix_report,
            "adaptive_red_vs_adaptive_blue_reduced_observability",
            "final_compromised_mean",
        )

        if baseline is None:
            continue
        if red_reduced is not None:
            red_penalties.append(round(red_reduced - baseline, 3))
        if blue_reduced is not None:
            blue_penalties.append(round(blue_reduced - baseline, 3))

    if not red_penalties and not blue_penalties:
        return {
            "sample_count": 0,
            "red_penalty_mean": None,
            "blue_penalty_mean": None,
            "combined_penalty_mean": None,
        }

    combined = red_penalties + blue_penalties
    return {
        "sample_count": len(combined),
        "red_penalty_mean": round(_mean(red_penalties), 3) if red_penalties else None,
        "blue_penalty_mean": round(_mean(blue_penalties), 3) if blue_penalties else None,
        "combined_penalty_mean": round(_mean(combined), 3),
    }


def build_default_stress_test_configs(
    *,
    seeds: tuple[int, ...] = (20260423, 20260424),
    horizon: int = 3,
) -> tuple[StressTestConfig, ...]:
    if not seeds:
        raise ValueError("seeds cannot be empty")
    if horizon < 1:
        raise ValueError("horizon must be >= 1")

    return (
        StressTestConfig(
            profile_id="scale_scenarios",
            label="Scale Scenarios Stress",
            scenario_paths=(
                "scenarios/baselines/rule_baseline.json",
                "scenarios/library/containment_stress.json",
                "scenarios/library/scale_chain_6.json",
            ),
            seeds=seeds,
            horizon=horizon,
            include_ablations=False,
            observation_noise_proxy=False,
            notes="scale pressure via larger topology set and multi-scenario batch.",
        ),
        StressTestConfig(
            profile_id="noise_observability_constraints",
            label="Noise and Observability Constraints",
            scenario_paths=(
                "scenarios/library/containment_stress.json",
                "scenarios/library/scale_chain_6.json",
            ),
            seeds=seeds,
            horizon=horizon,
            include_ablations=True,
            observation_noise_proxy=True,
            notes="uses reduced-observability ablations as a deterministic observation-noise proxy.",
        ),
    )


def run_stress_test_suite(
    *,
    profiles: tuple[StressTestConfig, ...] | None = None,
    runs_root: str | Path = "artifacts/runs",
    metrics_root: str | Path = "artifacts/metrics",
    reports_root: str | Path = "artifacts/reports",
) -> dict:
    selected_profiles = profiles if profiles is not None else build_default_stress_test_configs()
    if not selected_profiles:
        raise ValueError("profiles cannot be empty")

    profile_reports: list[dict] = []
    for profile in selected_profiles:
        profile_output = run_policy_experiment_matrix_batch(
            scenario_paths=list(profile.scenario_paths),
            seeds=list(profile.seeds),
            horizon=profile.horizon,
            runs_root=Path(runs_root) / profile.profile_id,
            metrics_root=Path(metrics_root) / profile.profile_id,
            reports_root=Path(reports_root) / profile.profile_id,
            include_ablations=profile.include_ablations,
        )
        batch_report = profile_output["report"]

        baseline_means: list[float] = []
        for scenario_report in batch_report.get("scenario_reports", []):
            matrix_report = scenario_report.get("report", {})
            baseline_value = _condition_metric(matrix_report, "rule_red_vs_rule_blue", "final_compromised_mean")
            if baseline_value is not None:
                baseline_means.append(round(baseline_value, 3))

        profile_summary = {
            "profile_id": profile.profile_id,
            "label": profile.label,
            "scenario_count": len(profile.scenario_paths),
            "seed_count": len(profile.seeds),
            "horizon": profile.horizon,
            "include_ablations": profile.include_ablations,
            "observation_noise_proxy": profile.observation_noise_proxy,
            "baseline_final_compromised_mean": round(_mean(baseline_means), 3),
            "baseline_final_compromised_max": round(max(baseline_means), 3) if baseline_means else 0.0,
        }
        if profile.observation_noise_proxy:
            profile_summary["observability_penalty"] = _compute_observability_penalty(batch_report)

        profile_reports.append(
            {
                "config": asdict(profile),
                "report_file": profile_output["report_file"],
                "report": batch_report,
                "summary": profile_summary,
            }
        )

    ranked_profiles = sorted(
        profile_reports,
        key=lambda item: (
            item["summary"]["baseline_final_compromised_mean"],
            item["summary"]["baseline_final_compromised_max"],
            item["summary"]["profile_id"],
        ),
    )

    suite_payload = {
        "suite_metadata": {
            "profile_count": len(profile_reports),
            "profiles": [report["summary"]["profile_id"] for report in profile_reports],
            "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        },
        "profile_reports": profile_reports,
        "profile_rankings": {
            "lowest_baseline_compromised": [
                {
                    "rank": index,
                    "profile_id": profile_report["summary"]["profile_id"],
                    "label": profile_report["summary"]["label"],
                    "baseline_final_compromised_mean": profile_report["summary"]["baseline_final_compromised_mean"],
                    "baseline_final_compromised_max": profile_report["summary"]["baseline_final_compromised_max"],
                    "include_ablations": profile_report["summary"]["include_ablations"],
                    "observation_noise_proxy": profile_report["summary"]["observation_noise_proxy"],
                }
                for index, profile_report in enumerate(ranked_profiles, start=1)
            ],
        },
    }

    report_dir = Path(reports_root)
    report_dir.mkdir(parents=True, exist_ok=True)
    report_file = report_dir / "stress_test_suite_report.json"
    report_file.write_text(json.dumps(suite_payload, indent=2, sort_keys=True), encoding="utf-8")

    return {
        "report_file": str(report_file),
        "report": suite_payload,
    }
