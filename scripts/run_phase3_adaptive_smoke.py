from __future__ import annotations

import json

from experiments.phase3_adaptive_comparison import run_phase3_adaptive_comparison
from visualization.reporting import write_phase3_markdown_summary


def main() -> None:
    result = run_phase3_adaptive_comparison(
        scenario_path="scenarios/baselines/phase2_rule_baseline.json",
        seeds=[20260329, 20260330],
        horizon=6,
    )
    markdown_path = write_phase3_markdown_summary(
        result["report"],
        "artifacts/reports/phase3_adaptive_comparison_summary.md",
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
