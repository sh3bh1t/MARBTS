from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from observability.replay import load_run_artifact_bundle

from .report_artifacts import build_report_payload


def _default_report_file(left_summary: dict[str, Any], right_summary: dict[str, Any], reports_root: str | Path) -> Path:
    file_name = f"comparative_report_{left_summary['run_id']}_vs_{right_summary['run_id']}.json"
    return Path(reports_root) / file_name


def _build_comparisons(left_summary: dict[str, Any], right_summary: dict[str, Any]) -> dict[str, Any]:
    return {
        "timesteps_count_delta": right_summary["timesteps_count"] - left_summary["timesteps_count"],
        "final_compromised_nodes_delta": right_summary["final_compromised_nodes"] - left_summary["final_compromised_nodes"],
        "blue_containment_actions_delta": right_summary["blue_containment_actions"] - left_summary["blue_containment_actions"],
        "first_containment_timestep_delta": right_summary["first_containment_timestep"] - left_summary["first_containment_timestep"],
        "sequence_hash_match": left_summary["sequence_hash"] == right_summary["sequence_hash"],
        "replay_sequence_hash_match": left_summary["replay_sequence_hash"] == right_summary["replay_sequence_hash"],
        "sequence_hash_integrity": left_summary["sequence_hash_matches"] and right_summary["sequence_hash_matches"],
    }


def generate_comparative_report(
    *,
    left_run_dir: str | Path,
    right_run_dir: str | Path,
    reports_root: str | Path = "artifacts/reports",
    figures_root: str | Path = "artifacts/figures",
    output_path: str | Path | None = None,
) -> dict[str, Any]:
    left_bundle = load_run_artifact_bundle(left_run_dir)
    right_bundle = load_run_artifact_bundle(right_run_dir)
    left_summary = left_bundle["summary"]
    right_summary = right_bundle["summary"]

    report_file = Path(output_path) if output_path is not None else _default_report_file(left_summary, right_summary, reports_root)
    report_file.parent.mkdir(parents=True, exist_ok=True)
    report_payload, figure_files, markdown_report = build_report_payload(
        report_file=report_file,
        figures_root=figures_root,
        left_summary=left_summary,
        right_summary=right_summary,
        left_bundle=left_bundle,
        right_bundle=right_bundle,
        comparisons=_build_comparisons(left_summary, right_summary),
    )

    report_file.write_text(json.dumps(report_payload, indent=2, sort_keys=True), encoding="utf-8")

    markdown_file = report_file.with_suffix(".md")
    markdown_file.write_text(markdown_report, encoding="utf-8")

    return {
        "report_file": str(report_file),
        "summary_file": str(markdown_file),
        "figure_files": figure_files,
        "report": report_payload,
    }