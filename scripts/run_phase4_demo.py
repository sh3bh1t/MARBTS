from __future__ import annotations

import json
from pathlib import Path

from experiments.phase3_unified_comparison import run_phase3_unified_comparison
from hart.models import AdaptivePolicyConfig
from simulation.artifact_loader import load_run_artifacts, reconstruct_run_replay, validate_run_artifacts
from visualization.replay_reports import write_phase4_dashboard_html, write_run_replay_markdown


def main() -> None:
    comparison = run_phase3_unified_comparison(
        scenario_path="scenarios/baselines/phase2_rule_baseline.json",
        seeds=[20260329],
        horizon=6,
        planner_config=AdaptivePolicyConfig(backend="planning", planning_depth=3),
        llm_config=AdaptivePolicyConfig(backend="openai", model_name="gpt-5-mini", reasoning_effort="low"),
    )

    first_run = comparison["report"]["runs"][0]
    run_artifacts = load_run_artifacts(first_run["run_dir"])
    validation_payload = validate_run_artifacts(run_artifacts)
    replay_frames = reconstruct_run_replay(run_artifacts)

    replay_path = write_run_replay_markdown(
        run_artifacts,
        replay_frames,
        Path("artifacts/reports") / f"phase4_replay_{run_artifacts['metadata']['run_id']}.md",
    )
    dashboard_path = write_phase4_dashboard_html(
        comparison["report"],
        validation_payload,
        Path(replay_path).name,
        Path("artifacts/reports") / "phase4_demo_dashboard.html",
    )

    print(
        json.dumps(
            {
                "comparison_report_file": comparison["report_file"],
                "replay_markdown_file": replay_path,
                "dashboard_html_file": dashboard_path,
            },
            indent=2,
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
