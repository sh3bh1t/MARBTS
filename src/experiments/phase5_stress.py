from __future__ import annotations

from dataclasses import asdict
from datetime import datetime, timezone
import json
from pathlib import Path

from experiments.phase3_unified_comparison import run_phase3_unified_comparison
from experiments.scenario_catalog import resolve_catalog_scenario_path, validate_scenario_catalog
from hart.models import AdaptivePolicyConfig, StressTestConfig


def load_stress_test_config(path: str | Path) -> StressTestConfig:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("stress test config root must be an object")

    return StressTestConfig(
        config_id=str(payload["config_id"]),
        scenario_ids=tuple(str(item) for item in payload["scenario_ids"]),
        seeds=tuple(int(seed) for seed in payload["seeds"]),
        horizon=int(payload["horizon"]),
        planner_depth=int(payload.get("planner_depth", 3)),
        include_llm_conditions=bool(payload.get("include_llm_conditions", True)),
        feature_flags={str(key): bool(value) for key, value in dict(payload.get("feature_flags", {})).items()},
    )


def run_phase5_stress_suite(
    *,
    catalog_path: str | Path,
    stress_config_path: str | Path,
    runs_root: str | Path = "artifacts/runs",
    reports_root: str | Path = "artifacts/reports",
) -> dict:
    catalog_entries = validate_scenario_catalog(catalog_path)
    stress_config = load_stress_test_config(stress_config_path)

    reports: list[dict] = []
    for scenario_id in stress_config.scenario_ids:
        scenario_path = resolve_catalog_scenario_path(catalog_path, scenario_id)
        planner_config = AdaptivePolicyConfig(
            backend="planning",
            planning_depth=stress_config.planner_depth,
            feature_flags=dict(stress_config.feature_flags),
        )
        llm_config = AdaptivePolicyConfig(
            backend="openai",
            model_name="gpt-5-mini",
            reasoning_effort="low",
            feature_flags=dict(stress_config.feature_flags),
        )
        report_output = run_phase3_unified_comparison(
            scenario_path=scenario_path,
            seeds=list(stress_config.seeds),
            horizon=stress_config.horizon,
            planner_config=planner_config,
            llm_config=llm_config,
            runs_root=Path(runs_root),
            reports_root=Path(reports_root),
        )
        reports.append(
            {
                "scenario_id": scenario_id,
                "report_file": report_output["report_file"],
                "report": report_output["report"],
            }
        )

    summary_payload = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "catalog_path": str(catalog_path),
        "stress_config": asdict(stress_config),
        "catalog_entry_count": len(catalog_entries),
        "reports": [
            {
                "scenario_id": item["scenario_id"],
                "report_file": item["report_file"],
                "aggregate_count": len(item["report"]["aggregates"]),
            }
            for item in reports
        ],
    }

    summary_dir = Path(reports_root)
    summary_dir.mkdir(parents=True, exist_ok=True)
    summary_file = summary_dir / f"phase5_stress_summary_{stress_config.config_id}.json"
    summary_file.write_text(json.dumps(summary_payload, indent=2, sort_keys=True), encoding="utf-8")
    return {"summary_file": str(summary_file), "summary": summary_payload}
