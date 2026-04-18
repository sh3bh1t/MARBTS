from __future__ import annotations

import json

from experiments.phase3_unified_comparison import run_phase3_unified_comparison
from hart.models import AdaptivePolicyConfig
from visualization.reporting import write_phase3_markdown_summary


def main() -> None:
    result = run_phase3_unified_comparison(
        scenario_path="scenarios/baselines/phase2_rule_baseline.json",
        seeds=[20260329],
        horizon=6,
        planner_config=AdaptivePolicyConfig(backend="planning", planning_depth=3),
        rl_config=AdaptivePolicyConfig(backend="rl", model_name="value_q_v1"),
        llm_config=AdaptivePolicyConfig(backend="openai", model_name="gpt-5-mini", reasoning_effort="low"),
    )
    markdown_path = write_phase3_markdown_summary(
        result["report"],
        "artifacts/reports/phase3_rl_comparison_summary.md",
    )
    print(json.dumps({"report_file": result["report_file"], "markdown_summary_file": markdown_path}, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
