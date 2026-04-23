from __future__ import annotations

from dataclasses import asdict
from datetime import datetime, timezone
import hashlib
import json
import re
from pathlib import Path
from typing import Any, Mapping, Sequence

from hart.models import AblationMatrix, ContainerExecutionConfig, PublicationMetricTable, ResearchArtifactManifest

from .policy_experiment_matrix import run_policy_experiment_matrix


def _sanitize_label(value: str) -> str:
    return re.sub(r"[^A-Za-z0-9._-]+", "_", value).strip("_") or "artifact"


def _format_number(value: float | int) -> str:
    if isinstance(value, int):
        return str(value)
    if float(value).is_integer():
        return str(int(round(float(value))))
    return f"{float(value):.3f}".rstrip("0").rstrip(".")


def _render_markdown_table(headers: Sequence[str], rows: Sequence[Sequence[Any]]) -> str:
    header_line = "| " + " | ".join(headers) + " |"
    separator_line = "| " + " | ".join("---" for _ in headers) + " |"
    body_lines = ["| " + " | ".join(str(cell) for cell in row) + " |" for row in rows]
    return "\n".join([header_line, separator_line, *body_lines])


def _summary_text(config: Mapping[str, Any] | None, *, kind: str) -> str:
    if not config:
        return "none"

    if kind == "ablation":
        flags: list[str] = []
        if config.get("no_planning"):
            flags.append("no_planning")
        if config.get("reduced_observability"):
            flags.append("reduced_observability")
        return ", ".join(flags) if flags else "baseline"

    flags = [f"h={config.get('planning_horizon', '?')}"]
    flags.append("decoy" if config.get("enable_decoy") else "no_decoy")
    flags.append("bluff" if config.get("enable_bluff") else "no_bluff")
    if config.get("reduced_observability"):
        flags.append("reduced_observability")
    return "; ".join(flags)


def _build_condition_tables(report: dict[str, Any]) -> tuple[PublicationMetricTable, ...]:
    aggregates = {aggregate["condition_id"]: aggregate for aggregate in report.get("condition_aggregates", [])}
    comparisons = {comparison["condition_id"]: comparison for comparison in report.get("comparison_to_baseline", [])}

    ranked_condition_ids = [entry["condition_id"] for entry in report.get("summary_rankings", {}).get("lowest_final_compromised", [])]
    if not ranked_condition_ids:
        ranked_condition_ids = sorted(
            aggregates,
            key=lambda condition_id: (
                aggregates[condition_id]["metric_bundle"]["final_compromised_mean"],
                condition_id,
            ),
        )

    primary_rows: list[tuple[Any, ...]] = []
    config_rows: list[tuple[Any, ...]] = []

    for rank, condition_id in enumerate(ranked_condition_ids, start=1):
        aggregate = aggregates[condition_id]
        metric_bundle = aggregate["metric_bundle"]
        comparison = comparisons.get(condition_id, {})

        primary_rows.append(
            (
                rank,
                aggregate["condition_id"],
                aggregate["condition_label"],
                f"{aggregate['red_policy']} vs {aggregate['blue_policy']}",
                _summary_text(aggregate.get("ablation"), kind="ablation"),
                _format_number(metric_bundle["final_compromised_mean"]),
                _format_number(metric_bundle["blue_containment_mean"]),
                _format_number(metric_bundle["deterministic_consistency_ratio"]),
                _format_number(comparison.get("delta_final_compromised_mean_vs_rule_rule", 0.0)),
                _format_number(comparison.get("delta_blue_containment_mean_vs_rule_rule", 0.0)),
            )
        )

        config_rows.append(
            (
                aggregate["condition_id"],
                aggregate["condition_label"],
                _summary_text(aggregate.get("red_ablation"), kind="ablation"),
                _summary_text(aggregate.get("blue_ablation"), kind="ablation"),
                _summary_text(aggregate.get("red_adaptive_config"), kind="adaptive"),
                _summary_text(aggregate.get("blue_adaptive_config"), kind="adaptive"),
            )
        )

    return (
        PublicationMetricTable(
            title="Primary Ranking",
            columns=(
                "Rank",
                "Condition ID",
                "Condition Label",
                "Policies",
                "Ablation Flags",
                "Final Compromised Mean",
                "Blue Containment Mean",
                "Deterministic Consistency Ratio",
                "Delta Compromised vs Baseline",
                "Delta Containment vs Baseline",
            ),
            rows=tuple(primary_rows),
        ),
        PublicationMetricTable(
            title="Condition Configuration",
            columns=(
                "Condition ID",
                "Condition Label",
                "Red Ablation",
                "Blue Ablation",
                "Red Adaptive Config",
                "Blue Adaptive Config",
            ),
            rows=tuple(config_rows),
        ),
    )


def build_container_execution_config(
    *,
    scenario_path: str | Path,
    seeds: Sequence[int],
    horizon: int,
    include_ablations: bool,
    image: str = "python:3.12-slim",
    working_directory: str = "/workspace/MARBTS",
) -> ContainerExecutionConfig:
    normalized_scenario_path = str(Path(scenario_path))
    normalized_seeds = tuple(int(seed) for seed in seeds)
    command = [
        "python",
        "scripts/run_ablation_report.py",
        "--scenario",
        normalized_scenario_path,
        "--seeds",
        ",".join(str(seed) for seed in normalized_seeds),
        "--horizon",
        str(horizon),
    ]
    if not include_ablations:
        command.append("--skip-ablations")

    pin_source = {
        "scenario_path": normalized_scenario_path,
        "seeds": list(normalized_seeds),
        "horizon": horizon,
        "include_ablations": include_ablations,
        "image": image,
        "working_directory": working_directory,
        "command": command,
    }
    config_pin = hashlib.sha256(json.dumps(pin_source, sort_keys=True).encode("utf-8")).hexdigest()[:16]

    return ContainerExecutionConfig(
        enabled=True,
        image=image,
        working_directory=working_directory,
        command=tuple(command),
        environment={"PYTHONPATH": "src"},
        config_pin=f"sha256:{config_pin}",
        notes="Optional reproducible execution profile for Phase 5 Increment 4.",
    )


def build_ablation_report_package(
    *,
    matrix_report: dict[str, Any],
    scenario_path: str | Path,
    source_report_file: str | Path,
    container_execution: ContainerExecutionConfig | None = None,
) -> tuple[AblationMatrix, str]:
    metadata = matrix_report.get("matrix_metadata", {})
    scenario_id = metadata.get("scenario_id", "unknown-scenario")
    scenario_version = metadata.get("scenario_version", "unknown-version")
    scenario_key = _sanitize_label(f"{scenario_id}__v{scenario_version}")
    publication_tables = _build_condition_tables(matrix_report)

    template_metadata = {
        "package_id": f"ablation_package_{scenario_key}",
        "scenario_id": scenario_id,
        "scenario_version": scenario_version,
        "scenario_path": str(Path(scenario_path)),
        "source_report_file": str(Path(source_report_file)),
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "condition_count": metadata.get("condition_count", len(matrix_report.get("conditions", []))),
        "seed_count": metadata.get("seed_count", 0),
        "horizon": metadata.get("horizon", 0),
        "include_ablations": metadata.get("include_ablations", True),
        "table_count": len(publication_tables),
        "containerized": container_execution.enabled if container_execution is not None else False,
    }

    ablation_matrix = AblationMatrix(
        template_metadata=template_metadata,
        publication_tables=publication_tables,
        comparison_to_baseline=tuple(matrix_report.get("comparison_to_baseline", [])),
        summary_rankings=matrix_report.get("summary_rankings", {}),
        container_execution=container_execution,
    )

    markdown_lines = [
        "# Ablation Report Template",
        "",
        f"Scenario: {template_metadata['scenario_id']} ({template_metadata['scenario_version']})",
        f"Scenario path: {template_metadata['scenario_path']}",
        f"Source matrix report: {template_metadata['source_report_file']}",
        "",
        "## Reproducibility Capsule",
        f"- Seeds: {matrix_report.get('matrix_metadata', {}).get('seeds', [])}",
        f"- Horizon: {template_metadata['horizon']}",
        f"- Include ablations: {template_metadata['include_ablations']}",
        f"- Containerized profile: {template_metadata['containerized']}",
    ]

    if container_execution is not None:
        markdown_lines.extend(
            [
                f"- Container image: {container_execution.image}",
                f"- Working directory: {container_execution.working_directory}",
                f"- Command: {' '.join(container_execution.command)}",
                f"- Config pin: {container_execution.config_pin}",
            ]
        )

    markdown_lines.extend(
        [
            "",
            "## Primary Ranking",
            _render_markdown_table(publication_tables[0].columns, publication_tables[0].rows),
            "",
            "## Condition Configuration",
            _render_markdown_table(publication_tables[1].columns, publication_tables[1].rows),
            "",
            "## Ranked Condition Notes",
        ]
    )

    for entry in ablation_matrix.summary_rankings.get("lowest_final_compromised", [])[:3]:
        metric_bundle = entry.get("metric_bundle", {})
        markdown_lines.append(
            "- "
            + f"{entry.get('rank', '?')}. {entry.get('condition_label', entry.get('condition_id', 'unknown'))} "
            + f"(final compromised mean={_format_number(metric_bundle.get('final_compromised_mean', 0.0))}, "
            + f"blue containment mean={_format_number(metric_bundle.get('blue_containment_mean', 0.0))})"
        )

    return ablation_matrix, "\n".join(markdown_lines)


def write_ablation_report_package(
    *,
    matrix_report: dict[str, Any],
    scenario_path: str | Path,
    source_report_file: str | Path,
    reports_root: str | Path = "artifacts/reports",
    container_execution: ContainerExecutionConfig | None = None,
) -> dict[str, Any]:
    ablation_matrix, markdown_report = build_ablation_report_package(
        matrix_report=matrix_report,
        scenario_path=scenario_path,
        source_report_file=source_report_file,
        container_execution=container_execution,
    )

    report_dir = Path(reports_root) / "ablation"
    report_dir.mkdir(parents=True, exist_ok=True)

    package_id = ablation_matrix.template_metadata["package_id"]
    template_file = report_dir / f"ablation_report_template_{_sanitize_label(package_id)}.json"
    markdown_file = report_dir / f"ablation_report_template_{_sanitize_label(package_id)}.md"
    manifest_file = report_dir / f"research_artifact_manifest_{_sanitize_label(package_id)}.json"
    container_profile_file = (
        report_dir / f"container_execution_profile_{_sanitize_label(package_id)}.json"
        if container_execution is not None
        else None
    )

    template_payload = asdict(ablation_matrix)
    template_file.write_text(json.dumps(template_payload, indent=2, sort_keys=True), encoding="utf-8")
    markdown_file.write_text(markdown_report, encoding="utf-8")

    artifact_files = [str(template_file), str(markdown_file)]
    if container_execution is not None and container_profile_file is not None:
        container_profile_file.write_text(json.dumps(asdict(container_execution), indent=2, sort_keys=True), encoding="utf-8")
        artifact_files.append(str(container_profile_file))

    manifest = ResearchArtifactManifest(
        manifest_id=package_id,
        manifest_metadata={
            **ablation_matrix.template_metadata,
            "artifact_count": len(artifact_files) + 1,
            "container_profile_file": str(container_profile_file) if container_profile_file is not None else None,
        },
        ablation_matrix_file=str(template_file),
        markdown_file=str(markdown_file),
        container_profile_file=str(container_profile_file) if container_profile_file is not None else None,
        artifact_files=tuple(artifact_files + [str(manifest_file)]),
    )
    manifest_file.write_text(json.dumps(asdict(manifest), indent=2, sort_keys=True), encoding="utf-8")

    return {
        "template_file": str(template_file),
        "markdown_file": str(markdown_file),
        "manifest_file": str(manifest_file),
        "container_profile_file": str(container_profile_file) if container_profile_file is not None else None,
        "template": template_payload,
        "manifest": asdict(manifest),
    }


def run_ablation_report_package(
    *,
    scenario_path: str | Path,
    seeds: list[int],
    horizon: int,
    runs_root: str | Path = "artifacts/runs",
    metrics_root: str | Path = "artifacts/metrics",
    reports_root: str | Path = "artifacts/reports",
    include_ablations: bool = True,
    containerized: bool = False,
    container_image: str = "python:3.12-slim",
    container_working_directory: str = "/workspace/MARBTS",
) -> dict[str, Any]:
    if not seeds:
        raise ValueError("seeds cannot be empty")

    matrix_output = run_policy_experiment_matrix(
        scenario_path=scenario_path,
        seeds=seeds,
        horizon=horizon,
        runs_root=runs_root,
        metrics_root=metrics_root,
        reports_root=reports_root,
        include_ablations=include_ablations,
    )

    container_execution = (
        build_container_execution_config(
            scenario_path=scenario_path,
            seeds=seeds,
            horizon=horizon,
            include_ablations=include_ablations,
            image=container_image,
            working_directory=container_working_directory,
        )
        if containerized
        else None
    )

    package_output = write_ablation_report_package(
        matrix_report=matrix_output["report"],
        scenario_path=scenario_path,
        source_report_file=matrix_output["report_file"],
        reports_root=reports_root,
        container_execution=container_execution,
    )

    return {
        "matrix_report_file": matrix_output["report_file"],
        "matrix_report": matrix_output["report"],
        **package_output,
    }