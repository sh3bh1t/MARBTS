from __future__ import annotations

from dataclasses import asdict
from datetime import datetime, timezone
import math
import re
from pathlib import Path
from typing import Any
from xml.sax.saxutils import escape

from hart.models import ExperimentSummary


_FIGURE_WIDTH = 1080
_FIGURE_HEIGHT = 420
_MARGIN_LEFT = 72
_MARGIN_RIGHT = 28
_MARGIN_TOP = 68
_MARGIN_BOTTOM = 72
_PALETTE = (
    "#1d4ed8",
    "#dc2626",
    "#0f766e",
    "#7c3aed",
)


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


def _svg_header(title: str, subtitle: str) -> list[str]:
    return [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{_FIGURE_WIDTH}" height="{_FIGURE_HEIGHT}" viewBox="0 0 {_FIGURE_WIDTH} {_FIGURE_HEIGHT}">',
        '<rect width="100%" height="100%" fill="#ffffff" />',
        f'<text x="{_MARGIN_LEFT}" y="28" font-size="22" font-weight="700" fill="#111827">{escape(title)}</text>',
        f'<text x="{_MARGIN_LEFT}" y="48" font-size="12" fill="#4b5563">{escape(subtitle)}</text>',
    ]


def _svg_footer() -> list[str]:
    return ["</svg>"]


def _render_svg_line_chart(
    *,
    title: str,
    subtitle: str,
    x_values: list[int],
    series: list[tuple[str, list[float | int], str]],
    y_label: str,
    x_label: str,
) -> str:
    chart_width = _FIGURE_WIDTH - _MARGIN_LEFT - _MARGIN_RIGHT
    chart_height = _FIGURE_HEIGHT - _MARGIN_TOP - _MARGIN_BOTTOM
    chart_left = _MARGIN_LEFT
    chart_top = _MARGIN_TOP
    chart_bottom = chart_top + chart_height
    chart_right = chart_left + chart_width
    max_x = max(x_values) if x_values else 0
    max_y = max((max(values) if values else 0 for _, values, _ in series), default=0)
    max_y = max(1, max_y)
    y_ticks = 4
    x_span = max(1, max_x)

    svg = _svg_header(title, subtitle)
    svg.append(
        f'<line x1="{chart_left}" y1="{chart_top}" x2="{chart_left}" y2="{chart_bottom}" stroke="#9ca3af" stroke-width="1.5" />'
    )
    svg.append(
        f'<line x1="{chart_left}" y1="{chart_bottom}" x2="{chart_right}" y2="{chart_bottom}" stroke="#9ca3af" stroke-width="1.5" />'
    )

    for index in range(y_ticks + 1):
        value = max_y * index / y_ticks
        y = chart_bottom - (value / max_y) * chart_height
        svg.append(f'<line x1="{chart_left}" y1="{y:.2f}" x2="{chart_right}" y2="{y:.2f}" stroke="#e5e7eb" stroke-width="1" />')
        svg.append(
            f'<text x="{chart_left - 10}" y="{y + 4:.2f}" text-anchor="end" font-size="11" fill="#4b5563">{_format_number(value)}</text>'
        )

    for x_value in x_values:
        x = chart_left + (x_value / x_span) * chart_width if x_span else chart_left
        svg.append(f'<line x1="{x:.2f}" y1="{chart_bottom}" x2="{x:.2f}" y2="{chart_bottom + 6}" stroke="#9ca3af" stroke-width="1" />')
        svg.append(
            f'<text x="{x:.2f}" y="{chart_bottom + 22}" text-anchor="middle" font-size="11" fill="#4b5563">{x_value}</text>'
        )

    svg.append(
        f'<text x="{chart_left - 46}" y="{chart_top + chart_height / 2:.2f}" transform="rotate(-90 {chart_left - 46},{chart_top + chart_height / 2:.2f})" font-size="12" fill="#374151">{escape(y_label)}</text>'
    )
    svg.append(
        f'<text x="{chart_left + chart_width / 2:.2f}" y="{_FIGURE_HEIGHT - 22}" text-anchor="middle" font-size="12" fill="#374151">{escape(x_label)}</text>'
    )

    legend_x = chart_left + 12
    legend_y = 56
    for label_index, (label, values, color) in enumerate(series):
        points = []
        for x_value, value in zip(x_values, values, strict=False):
            x = chart_left + (x_value / x_span) * chart_width if x_span else chart_left
            y = chart_bottom - (float(value) / max_y) * chart_height
            points.append(f"{x:.2f},{y:.2f}")

        if points:
            svg.append(
                f'<polyline fill="none" stroke="{color}" stroke-width="3" points="{" ".join(points)}" />'
            )
        for x_value, value in zip(x_values, values, strict=False):
            x = chart_left + (x_value / x_span) * chart_width if x_span else chart_left
            y = chart_bottom - (float(value) / max_y) * chart_height
            svg.append(f'<circle cx="{x:.2f}" cy="{y:.2f}" r="3.5" fill="{color}" />')

        legend_offset = legend_y + (label_index * 18)
        svg.append(f'<rect x="{legend_x}" y="{legend_offset - 10}" width="12" height="12" fill="{color}" />')
        svg.append(
            f'<text x="{legend_x + 18}" y="{legend_offset}" font-size="12" fill="#374151">{escape(label)}</text>'
        )

    svg.extend(_svg_footer())
    return "\n".join(svg)


def _render_svg_bar_chart(
    *,
    title: str,
    subtitle: str,
    categories: list[str],
    values: list[float | int],
    y_label: str,
    value_suffix: str = "",
) -> str:
    chart_width = _FIGURE_WIDTH - _MARGIN_LEFT - _MARGIN_RIGHT
    chart_height = _FIGURE_HEIGHT - _MARGIN_TOP - _MARGIN_BOTTOM
    chart_left = _MARGIN_LEFT
    chart_top = _MARGIN_TOP
    chart_bottom = chart_top + chart_height
    chart_right = chart_left + chart_width
    max_value = max((float(value) for value in values if value >= 0), default=0.0)
    max_value = max(1.0, max_value)
    bar_width = chart_width / max(1, len(categories) * 1.4)
    gap = bar_width * 0.4

    svg = _svg_header(title, subtitle)
    svg.append(
        f'<line x1="{chart_left}" y1="{chart_top}" x2="{chart_left}" y2="{chart_bottom}" stroke="#9ca3af" stroke-width="1.5" />'
    )
    svg.append(
        f'<line x1="{chart_left}" y1="{chart_bottom}" x2="{chart_right}" y2="{chart_bottom}" stroke="#9ca3af" stroke-width="1.5" />'
    )

    y_ticks = 4
    for index in range(y_ticks + 1):
        value = max_value * index / y_ticks
        y = chart_bottom - (value / max_value) * chart_height
        svg.append(f'<line x1="{chart_left}" y1="{y:.2f}" x2="{chart_right}" y2="{y:.2f}" stroke="#e5e7eb" stroke-width="1" />')
        svg.append(
            f'<text x="{chart_left - 10}" y="{y + 4:.2f}" text-anchor="end" font-size="11" fill="#4b5563">{_format_number(value)}</text>'
        )

    svg.append(
        f'<text x="{chart_left - 46}" y="{chart_top + chart_height / 2:.2f}" transform="rotate(-90 {chart_left - 46},{chart_top + chart_height / 2:.2f})" font-size="12" fill="#374151">{escape(y_label)}</text>'
    )

    for index, (category, value) in enumerate(zip(categories, values, strict=False)):
        x = chart_left + index * (bar_width + gap) + gap / 2
        if value >= 0:
            bar_height = (float(value) / max_value) * chart_height
            bar_y = chart_bottom - bar_height
            svg.append(f'<rect x="{x:.2f}" y="{bar_y:.2f}" width="{bar_width:.2f}" height="{bar_height:.2f}" rx="6" fill="{_PALETTE[index % len(_PALETTE)]}" />')
            svg.append(
                f'<text x="{x + bar_width / 2:.2f}" y="{bar_y - 8:.2f}" text-anchor="middle" font-size="12" fill="#111827">{_format_number(value)}{escape(value_suffix)}</text>'
            )
        else:
            svg.append(
                f'<rect x="{x:.2f}" y="{chart_bottom - 2:.2f}" width="{bar_width:.2f}" height="2" rx="1" fill="#9ca3af" />'
            )
            svg.append(
                f'<text x="{x + bar_width / 2:.2f}" y="{chart_bottom - 8:.2f}" text-anchor="middle" font-size="12" fill="#6b7280">N/A</text>'
            )

        svg.append(
            f'<text x="{x + bar_width / 2:.2f}" y="{chart_bottom + 20}" text-anchor="middle" font-size="11" fill="#374151">{escape(category)}</text>'
        )

    svg.append(
        f'<text x="{chart_left + chart_width / 2:.2f}" y="{_FIGURE_HEIGHT - 22}" text-anchor="middle" font-size="12" fill="#374151">Run</text>'
    )
    svg.extend(_svg_footer())
    return "\n".join(svg)


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

    compromise_svg = _render_svg_line_chart(
        title="Compromise Trend",
        subtitle=f"{left_summary['run_id']} vs {right_summary['run_id']}",
        x_values=x_values,
        series=[
            (left_summary["run_id"], left_compromise_values, _PALETTE[0]),
            (right_summary["run_id"], right_compromise_values, _PALETTE[1]),
        ],
        y_label="Compromised nodes",
        x_label="Timestep",
    )
    compromise_trend_file.write_text(compromise_svg, encoding="utf-8")

    defense_efficiency_svg = _render_svg_bar_chart(
        title="Defense Efficiency",
        subtitle="Containment-to-compromise ratio by run",
        categories=[left_summary["run_id"], right_summary["run_id"]],
        values=[
            left_analysis["defense_efficiency"]["containment_to_compromise_ratio"],
            right_analysis["defense_efficiency"]["containment_to_compromise_ratio"],
        ],
        y_label="Containment / compromise ratio",
    )
    defense_efficiency_file.write_text(defense_efficiency_svg, encoding="utf-8")

    response_latency_svg = _render_svg_bar_chart(
        title="Response Latency",
        subtitle="Gap between first compromise and first containment",
        categories=[left_summary["run_id"], right_summary["run_id"]],
        values=[left_analysis["response_latency"], right_analysis["response_latency"]],
        y_label="Timestep gap",
        value_suffix="t",
    )
    response_latency_file.write_text(response_latency_svg, encoding="utf-8")

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
