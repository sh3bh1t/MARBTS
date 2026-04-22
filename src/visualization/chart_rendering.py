from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Sequence

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt


@dataclass(frozen=True)
class FigureTheme:
    figure_size: tuple[float, float] = (10.8, 4.2)
    dpi: int = 144
    primary_color: str = "#1d4ed8"
    secondary_color: str = "#dc2626"
    background_color: str = "#ffffff"
    title_color: str = "#111827"
    text_color: str = "#374151"
    grid_color: str = "#e5e7eb"
    spine_color: str = "#cbd5e1"


DEFAULT_THEME = FigureTheme()


def _configure_axes(ax: plt.Axes, theme: FigureTheme) -> None:
    ax.set_facecolor(theme.background_color)
    ax.grid(True, axis="y", color=theme.grid_color, linewidth=1)
    ax.set_axisbelow(True)
    for spine_name in ("top", "right"):
        ax.spines[spine_name].set_visible(False)
    for spine_name in ("left", "bottom"):
        ax.spines[spine_name].set_color(theme.spine_color)
    ax.tick_params(colors=theme.text_color)


def _write_figure(fig: plt.Figure, output_path: str | Path) -> str:
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.tight_layout(rect=(0, 0, 1, 0.94))
    fig.savefig(path, format="svg", facecolor="white")
    plt.close(fig)
    return str(path)


def _format_value(value: float | int) -> str:
    if value < 0:
        return "N/A"
    if isinstance(value, int) or float(value).is_integer():
        return str(int(round(float(value))))
    return f"{float(value):.3f}".rstrip("0").rstrip(".")


def render_compromise_trend_figure(
    *,
    output_path: str | Path,
    left_label: str,
    left_values: Sequence[float | int],
    right_label: str,
    right_values: Sequence[float | int],
    title: str,
    subtitle: str,
    theme: FigureTheme = DEFAULT_THEME,
) -> str:
    fig, ax = plt.subplots(figsize=theme.figure_size, dpi=theme.dpi)
    _configure_axes(ax, theme)

    left_points = list(range(len(left_values)))
    right_points = list(range(len(right_values)))
    ax.plot(left_points, left_values, marker="o", linewidth=2.5, color=theme.primary_color, label=left_label)
    ax.plot(right_points, right_values, marker="o", linewidth=2.5, color=theme.secondary_color, label=right_label)

    ax.set_xlabel("Timestep", color=theme.text_color)
    ax.set_ylabel("Compromised nodes", color=theme.text_color)
    ax.set_title(title, loc="left", pad=18, color=theme.title_color, fontsize=15, fontweight="bold")
    fig.text(0.06, 0.915, subtitle, ha="left", va="top", color=theme.text_color, fontsize=10)
    ax.legend(frameon=False, loc="upper left")
    ax.margins(x=0.04)
    return _write_figure(fig, output_path)


def render_comparison_bar_figure(
    *,
    output_path: str | Path,
    labels: Sequence[str],
    values: Sequence[float | int],
    title: str,
    subtitle: str,
    y_label: str,
    value_suffix: str = "",
    theme: FigureTheme = DEFAULT_THEME,
) -> str:
    fig, ax = plt.subplots(figsize=theme.figure_size, dpi=theme.dpi)
    _configure_axes(ax, theme)

    plotted_values = [float(value) if value >= 0 else 0.0 for value in values]
    bars = ax.bar(labels, plotted_values, color=[theme.primary_color, theme.secondary_color][: len(labels)], width=0.55)

    ax.set_ylabel(y_label, color=theme.text_color)
    ax.set_title(title, loc="left", pad=18, color=theme.title_color, fontsize=15, fontweight="bold")
    fig.text(0.06, 0.915, subtitle, ha="left", va="top", color=theme.text_color, fontsize=10)

    max_value = max(plotted_values) if plotted_values else 0.0
    upper_bound = max(1.0, max_value * 1.25)
    ax.set_ylim(0, upper_bound)

    for bar, raw_value in zip(bars, values, strict=False):
        height = bar.get_height()
        label_text = _format_value(raw_value)
        offset = upper_bound * 0.03 if height > 0 else upper_bound * 0.04
        ax.text(
            bar.get_x() + bar.get_width() / 2,
            height + offset,
            f"{label_text}{value_suffix}",
            ha="center",
            va="bottom",
            color=theme.text_color,
            fontsize=11,
        )
        if raw_value < 0:
            ax.text(
                bar.get_x() + bar.get_width() / 2,
                upper_bound * 0.06,
                "N/A",
                ha="center",
                va="bottom",
                color=theme.text_color,
                fontsize=10,
                fontstyle="italic",
            )

    return _write_figure(fig, output_path)
