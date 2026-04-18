from __future__ import annotations

from pathlib import Path


def write_phase3_markdown_summary(report_payload: dict, output_path: str | Path) -> str:
    lines = [
        "# Phase 3 Adaptive Comparison",
        "",
        f"- Scenario: `{report_payload['scenario_id']}`",
        f"- Version: `{report_payload['scenario_version']}`",
        f"- Horizon: `{report_payload['horizon']}`",
        f"- Seeds: `{','.join(str(seed) for seed in report_payload['seeds'])}`",
        "",
        "## Aggregate Results",
        "",
    ]

    for aggregate in report_payload["aggregates"]:
        extra_fields: list[str] = []
        if "planning_depth" in aggregate:
            extra_fields.append(f"planning_depth={aggregate['planning_depth']}")
        if "model_name" in aggregate:
            extra_fields.append(f"model_name={aggregate['model_name']}")
        if "reasoning_effort" in aggregate:
            extra_fields.append(f"reasoning_effort={aggregate['reasoning_effort']}")

        lines.append(
            "- "
            f"{aggregate['condition_id']}: mean_final_compromised_nodes={aggregate['mean_final_compromised_nodes']}, "
            f"range=[{aggregate['min_final_compromised_nodes']}, {aggregate['max_final_compromised_nodes']}]"
            + (", " + ", ".join(extra_fields) if extra_fields else "")
        )

    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return str(output)
