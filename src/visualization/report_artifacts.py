from __future__ import annotations

from dataclasses import asdict
from datetime import datetime, timezone
import math
import re
from pathlib import Path
from typing import Any

from hart.models import ExperimentSummary

from .chart_rendering import render_compromise_trend_figure, render_comparison_bar_figure


def _sanitize_label(value: str) -> str:
    return re.sub(r"[^A-Za-z0-9._-]+", "_", value).strip("_") or "artifact"


def _artifact_stem(report_file: Path) -> str:
    return report_file.stem


def _format_number(value: float | int) -> str:
    if isinstance(value, int):
        return str(value)

    if math.isclose(value, round(value)):
        return str(int(round(value)))

    return f"{value:.3f}".rstrip("0").rstrip(".")


def _render_markdown_table(headers: tuple[str, ...], rows: list[tuple[Any, ...]]) -> str:
    header_line = "| " + " | ".join(headers) + " |"
    separator_line = "| " + " | ".join("---" for _ in headers) + " |"
    body_lines = ["| " + " | ".join(str(cell) for cell in row) + " |" for row in rows]
    return "\n".join([header_line, separator_line, *body_lines])


def _run_compromise_series(frames: tuple[Any, ...]) -> dict[str, list[float | int]]:
    return {
        "timestep": [frame.timestep for frame in frames],
        "compromised_nodes": [frame.metric_delta.compromised_nodes_after for frame in frames],
    }


def _find_first_timestep(frames: tuple[Any, ...], predicate: Any) -> int | None:
    for frame in frames:
        if predicate(frame):
            return frame.timestep
    return None


def _build_run_analysis(summary: dict[str, Any], frames: tuple[Any, ...]) -> dict[str, Any]:
    compromise_series = _run_compromise_series(frames)
    first_compromise_timestep = _find_first_timestep(frames, lambda frame: frame.metric_delta.compromised_nodes_after > 0)
    first_containment_timestep = summary["first_containment_timestep"] if summary["first_containment_timestep"] >= 0 else None

    if first_compromise_timestep is None or first_containment_timestep is None:
        response_latency = -1
    else:
        response_latency = max(0, first_containment_timestep - first_compromise_timestep)

    final_compromised_nodes = summary["final_compromised_nodes"]
    blue_containment_actions = summary["blue_containment_actions"]
    containment_to_compromise_ratio = (
        round(blue_containment_actions / max(1, final_compromised_nodes), 3)
        if blue_containment_actions or final_compromised_nodes
        else 0.0
    )

    return {
        "run_id": summary["run_id"],
        "scenario_id": summary["scenario_id"],
        "timestep_count": summary["timesteps_count"],
        "compromise_trend": compromise_series,
        "first_compromise_timestep": first_compromise_timestep if first_compromise_timestep is not None else -1,
        "first_containment_timestep": summary["first_containment_timestep"],
        "response_latency": response_latency,
        "defense_efficiency": {
            "blue_containment_actions": blue_containment_actions,
            "final_compromised_nodes": final_compromised_nodes,
            "containment_to_compromise_ratio": containment_to_compromise_ratio,
        },
    }


def _build_comparison_rows(left_analysis: dict[str, Any], right_analysis: dict[str, Any], comparisons: dict[str, Any]) -> list[tuple[str, str, str, str]]:
    return [
        (
            "Final compromised nodes",
            _format_number(left_analysis["defense_efficiency"]["final_compromised_nodes"]),
            _format_number(right_analysis["defense_efficiency"]["final_compromised_nodes"]),
            _format_number(comparisons["final_compromised_nodes_delta"]),
        ),
        (
            "Blue containment actions",
            _format_number(left_analysis["defense_efficiency"]["blue_containment_actions"]),
            _format_number(right_analysis["defense_efficiency"]["blue_containment_actions"]),
            _format_number(comparisons["blue_containment_actions_delta"]),
        ),
        (
            "First containment timestep",
            _format_number(left_analysis["first_containment_timestep"]),
            _format_number(right_analysis["first_containment_timestep"]),
            _format_number(comparisons["first_containment_timestep_delta"]),
        ),
        (
            "Response latency",
            _format_number(left_analysis["response_latency"]),
            _format_number(right_analysis["response_latency"]),
            _format_number(right_analysis["response_latency"] - left_analysis["response_latency"]),
        ),
        (
            "Containment-to-compromise ratio",
            _format_number(left_analysis["defense_efficiency"]["containment_to_compromise_ratio"]),
            _format_number(right_analysis["defense_efficiency"]["containment_to_compromise_ratio"]),
            _format_number(
                right_analysis["defense_efficiency"]["containment_to_compromise_ratio"]
                - left_analysis["defense_efficiency"]["containment_to_compromise_ratio"]
            ),
        ),
    ]


def _build_comparison_rows(left_analysis: dict[str, Any], right_analysis: dict[str, Any], comparisons: dict[str, Any]) -> list[tuple[str, str, str, str]]:
    return [
        (
            "Final compromised nodes",
            _format_number(left_analysis["defense_efficiency"]["final_compromised_nodes"]),
            _format_number(right_analysis["defense_efficiency"]["final_compromised_nodes"]),
            _format_number(comparisons["final_compromised_nodes_delta"]),
        ),
        (
            "Blue containment actions",
            _format_number(left_analysis["defense_efficiency"]["blue_containment_actions"]),
            _format_number(right_analysis["defense_efficiency"]["blue_containment_actions"]),
            _format_number(comparisons["blue_containment_actions_delta"]),
        ),
        (
            "First containment timestep",
            _format_number(left_analysis["first_containment_timestep"]),
            _format_number(right_analysis["first_containment_timestep"]),
            _format_number(comparisons["first_containment_timestep_delta"]),
        ),
        (
            "Response latency",
            _format_number(left_analysis["response_latency"]),
            _format_number(right_analysis["response_latency"]),
            _format_number(right_analysis["response_latency"] - left_analysis["response_latency"]),
        ),
        (
            "Containment-to-compromise ratio",
            _format_number(left_analysis["defense_efficiency"]["containment_to_compromise_ratio"]),
            _format_number(right_analysis["defense_efficiency"]["containment_to_compromise_ratio"]),
            _format_number(
                right_analysis["defense_efficiency"]["containment_to_compromise_ratio"]
                - left_analysis["defense_efficiency"]["containment_to_compromise_ratio"]
            ),
        ),
    ]


def build_report_payload(
    *,
    report_file: Path,
    figures_root: str | Path,
    left_summary: dict[str, Any],
    right_summary: dict[str, Any],
    left_bundle: dict[str, Any],
    right_bundle: dict[str, Any],
    comparisons: dict[str, Any],
) -> tuple[dict[str, Any], dict[str, str], str]:
    left_analysis = _build_run_analysis(left_summary, left_bundle["frames"])
    right_analysis = _build_run_analysis(right_summary, right_bundle["frames"])
    comparison_rows = _build_comparison_rows(left_analysis, right_analysis, comparisons)

    report_stem = _sanitize_label(_artifact_stem(report_file))
    figure_root = Path(figures_root)
    figure_root.mkdir(parents=True, exist_ok=True)

    compromise_trend_file = figure_root / f"{report_stem}_compromise_trend.svg"
    defense_efficiency_file = figure_root / f"{report_stem}_defense_efficiency.svg"
    response_latency_file = figure_root / f"{report_stem}_response_latency.svg"

    left_compromise_values = left_analysis["compromise_trend"]["compromised_nodes"]
    right_compromise_values = right_analysis["compromise_trend"]["compromised_nodes"]
    max_timestep = max(len(left_compromise_values), len(right_compromise_values))
    x_values = list(range(max_timestep))

    render_compromise_trend_figure(
        output_path=compromise_trend_file,
        left_label=left_summary["run_id"],
        left_values=left_compromise_values,
        right_label=right_summary["run_id"],
        right_values=right_compromise_values,
        title="Compromise Trend",
        subtitle=f"{left_summary['run_id']} vs {right_summary['run_id']}",
    )

    render_comparison_bar_figure(
        output_path=defense_efficiency_file,
        labels=[left_summary["run_id"], right_summary["run_id"]],
        values=[
            left_analysis["defense_efficiency"]["containment_to_compromise_ratio"],
            right_analysis["defense_efficiency"]["containment_to_compromise_ratio"],
        ],
        title="Defense Efficiency",
        subtitle="Containment-to-compromise ratio by run",
        y_label="Containment / compromise ratio",
    )

    render_comparison_bar_figure(
        output_path=response_latency_file,
        labels=[left_summary["run_id"], right_summary["run_id"]],
        values=[left_analysis["response_latency"], right_analysis["response_latency"]],
        title="Response Latency",
        subtitle="Gap between first compromise and first containment",
        y_label="Timestep gap",
    )

    report_summary = ExperimentSummary(
        scenario_id=f"{left_summary['scenario_id']}__vs__{right_summary['scenario_id']}",
        report_file=str(report_file),
        generated_at_utc=datetime.now(timezone.utc).isoformat(),
        metric_names=(
            "compromise_trend",
            "defense_efficiency",
            "response_latency",
            "sequence_hash_match",
        ),
    )

    figure_files = {
        "compromise_trend": str(compromise_trend_file),
        "defense_efficiency": str(defense_efficiency_file),
        "response_latency": str(response_latency_file),
    }

    report_payload = {
        "report_summary": asdict(report_summary),
        "left_run": left_summary,
        "right_run": right_summary,
        "comparisons": {
            **comparisons,
            "response_latency_delta": right_analysis["response_latency"] - left_analysis["response_latency"],
            "containment_to_compromise_ratio_delta": (
                right_analysis["defense_efficiency"]["containment_to_compromise_ratio"]
                - left_analysis["defense_efficiency"]["containment_to_compromise_ratio"]
            ),
        },
        "analysis": {
            "left_run": left_analysis,
            "right_run": right_analysis,
            "comparison_rows": comparison_rows,
        },
        "visualizations": {
            "compromise_trend": {
                "figure_file": figure_files["compromise_trend"],
                "series": {
                    left_summary["run_id"]: left_compromise_values,
                    right_summary["run_id"]: right_compromise_values,
                },
            },
            "defense_efficiency": {
                "figure_file": figure_files["defense_efficiency"],
                "metric": "containment_to_compromise_ratio",
                "values": {
                    left_summary["run_id"]: left_analysis["defense_efficiency"]["containment_to_compromise_ratio"],
                    right_summary["run_id"]: right_analysis["defense_efficiency"]["containment_to_compromise_ratio"],
                },
            },
            "response_latency": {
                "figure_file": figure_files["response_latency"],
                "metric": "response_latency",
                "values": {
                    left_summary["run_id"]: left_analysis["response_latency"],
                    right_summary["run_id"]: right_analysis["response_latency"],
                },
            },
        },
    }

    markdown_rows = _build_comparison_rows(left_analysis, right_analysis, comparisons)
    defense_rows = [
        (
            left_analysis["run_id"],
            _format_number(left_analysis["defense_efficiency"]["blue_containment_actions"]),
            _format_number(left_analysis["defense_efficiency"]["final_compromised_nodes"]),
            _format_number(left_analysis["defense_efficiency"]["containment_to_compromise_ratio"]),
            _format_number(left_analysis["first_containment_timestep"]),
            _format_number(left_analysis["response_latency"]),
        ),
        (
            right_analysis["run_id"],
            _format_number(right_analysis["defense_efficiency"]["blue_containment_actions"]),
            _format_number(right_analysis["defense_efficiency"]["final_compromised_nodes"]),
            _format_number(right_analysis["defense_efficiency"]["containment_to_compromise_ratio"]),
            _format_number(right_analysis["first_containment_timestep"]),
            _format_number(right_analysis["response_latency"]),
        ),
    ]

    markdown_lines = [
        "# Comparative Report",
        "",
        f"Scenario pair: {report_payload['report_summary']['scenario_id']}",
        "",
        "## Comparison Overview",
        _render_markdown_table(("Metric", "Left Run", "Right Run", "Delta"), markdown_rows),
        "",
        "## Defense Efficiency Table",
        _render_markdown_table(
            (
                "Run ID",
                "Blue containment actions",
                "Final compromised nodes",
                "Containment/compromise ratio",
                "First containment timestep",
                "Response latency",
            ),
            defense_rows,
        ),
        "",
        "## Figure Outputs",
        f"- Compromise trend: {figure_files['compromise_trend']}",
        f"- Defense efficiency: {figure_files['defense_efficiency']}",
        f"- Response latency: {figure_files['response_latency']}",
        "",
        "## Trend Notes",
        f"- Left compromise trend: {', '.join(_format_number(value) for value in left_compromise_values)}",
        f"- Right compromise trend: {', '.join(_format_number(value) for value in right_compromise_values)}",
    ]
    markdown_report = "\n".join(markdown_lines) + "\n"

    return report_payload, figure_files, markdown_report
