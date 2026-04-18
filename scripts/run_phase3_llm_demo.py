from __future__ import annotations

import json

from experiments.phase3_llm_comparison import run_phase3_llm_comparison
from hart.models import AdaptivePolicyConfig
from visualization.reporting import write_phase3_markdown_summary


def main() -> None:
    llm_config = AdaptivePolicyConfig(
        backend="openai",
        model_name="gpt-5-mini",
        reasoning_effort="low",
        fallback_backend="planning",
        feature_flags={"require_live_llm": True},
    )
    result = run_phase3_llm_comparison(
        scenario_path="scenarios/baselines/phase2_rule_baseline.json",
        seeds=[20260329],
        horizon=6,
        llm_config=llm_config,
    )
    markdown_path = write_phase3_markdown_summary(
        result["report"],
        "artifacts/reports/phase3_llm_comparison_summary.md",
    )
    print(
        json.dumps(
            {
                "report_file": result["report_file"],
                "markdown_summary_file": markdown_path,
            },
            indent=2,
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
