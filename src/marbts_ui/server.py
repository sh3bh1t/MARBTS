from __future__ import annotations

import argparse
import dataclasses
from enum import Enum
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import mimetypes
from pathlib import Path
import subprocess
from typing import Any, Mapping
from urllib.parse import parse_qs, unquote, urlparse

from agents.adaptive.planning import AdaptivePlanningPolicy
from agents.blue.rule_based import RuleBasedBluePolicy
from agents.interfaces.policy import PolicyRegistry
from agents.red.rule_based import RuleBasedRedPolicy
from environment.graph_builder import build_graph_from_scenario
from experiments.ablation_report import run_ablation_report_package
from experiments.multi_seed_report import run_multi_seed_report
from experiments.policy_experiment_matrix import (
    run_policy_experiment_matrix,
    run_policy_experiment_matrix_batch,
)
from experiments.stress_test_suite import build_default_stress_test_configs, run_stress_test_suite
from hart.enums import ActorType
from hart.models import AdaptivePolicyConfig
from metrics.baseline_metrics import compute_baseline_metrics, write_baseline_metrics_artifact
from observability.replay import load_run_artifact_bundle
from schemas.catalog import build_scenario_catalog, select_latest_scenario_entries
from schemas.scenario import load_scenario_file, validate_scenario_dict
from simulation.kernel import run_turn_based_simulation
from simulation.log_writer import write_run_artifacts
from utils.container_specs import (
    DEFAULT_COMPOSE_FILE,
    build_default_container_execution_specs,
    build_docker_compose_run_command,
    get_container_execution_spec,
)
from utils.release_validation import run_release_validation
from utils.runtime_presets import load_experiment_preset, load_seed_bundle
from visualization.comparative_report import generate_comparative_report


DEFAULT_SCENARIO_PATH = "scenarios/baselines/rule_baseline.json"
DEFAULT_RUNS_ROOT = "artifacts/runs"
DEFAULT_METRICS_ROOT = "artifacts/metrics"
DEFAULT_REPORTS_ROOT = "artifacts/reports"
DEFAULT_FIGURES_ROOT = "artifacts/figures"
MAX_BODY_BYTES = 5 * 1024 * 1024
MAX_ARTIFACT_BYTES = 8 * 1024 * 1024


class ApiError(Exception):
    def __init__(self, message: str, status: HTTPStatus = HTTPStatus.BAD_REQUEST) -> None:
        super().__init__(message)
        self.status = status


def _detect_project_root() -> Path:
    candidate = Path(__file__).resolve()
    for parent in [candidate.parent, *candidate.parents]:
        if (parent / "pyproject.toml").exists():
            return parent
    return Path.cwd()


PROJECT_ROOT = _detect_project_root().resolve()
STATIC_ROOT = Path(__file__).resolve().parent / "static"
TMP_ROOT = Path("/tmp").resolve()


def _is_relative_to(path: Path, parent: Path) -> bool:
    try:
        path.resolve().relative_to(parent.resolve())
    except ValueError:
        return False
    return True


def _relative_path(path: str | Path) -> str:
    resolved = Path(path).resolve()
    try:
        return resolved.relative_to(PROJECT_ROOT).as_posix()
    except ValueError:
        return str(resolved)


def _resolve_workspace_path(
    raw_path: Any,
    default_path: str,
    *,
    allow_tmp: bool = False,
    must_exist: bool = False,
) -> Path:
    value = default_path if raw_path in (None, "") else str(raw_path)
    path = Path(value).expanduser()
    if not path.is_absolute():
        path = PROJECT_ROOT / path
    resolved = path.resolve()

    allowed_roots = [PROJECT_ROOT]
    if allow_tmp:
        allowed_roots.append(TMP_ROOT)

    if not any(_is_relative_to(resolved, root) for root in allowed_roots):
        allowed = ", ".join(str(root) for root in allowed_roots)
        raise ApiError(f"path must stay inside one of: {allowed}")
    if must_exist and not resolved.exists():
        raise ApiError(f"path does not exist: {_relative_path(resolved)}", HTTPStatus.NOT_FOUND)
    return resolved


def _json_safe(value: Any) -> Any:
    if dataclasses.is_dataclass(value) and not isinstance(value, type):
        return _json_safe(dataclasses.asdict(value))
    if isinstance(value, Enum):
        return value.value
    if isinstance(value, Path):
        return _relative_path(value)
    if isinstance(value, Mapping):
        return {str(key): _json_safe(item) for key, item in value.items()}
    if isinstance(value, (tuple, list)):
        return [_json_safe(item) for item in value]
    if isinstance(value, set):
        return sorted(_json_safe(item) for item in value)
    return value


def _parse_seeds(raw_value: Any, default: list[int]) -> list[int]:
    if raw_value in (None, ""):
        return list(default)
    if isinstance(raw_value, str):
        tokens = [token.strip() for token in raw_value.split(",") if token.strip()]
    elif isinstance(raw_value, int):
        tokens = [raw_value]
    elif isinstance(raw_value, (list, tuple)):
        tokens = list(raw_value)
    else:
        raise ApiError("seeds must be a comma-separated string or list of integers")

    if not tokens:
        raise ApiError("seeds cannot be empty")
    try:
        seeds = [int(token) for token in tokens]
    except (TypeError, ValueError) as exc:
        raise ApiError("seeds must contain only integers") from exc
    if any(seed < 0 for seed in seeds):
        raise ApiError("seeds must be >= 0")
    return seeds


def _parse_horizon(raw_value: Any, default: int) -> int:
    if raw_value in (None, ""):
        return default
    try:
        horizon = int(raw_value)
    except (TypeError, ValueError) as exc:
        raise ApiError("horizon must be an integer") from exc
    if horizon < 1:
        raise ApiError("horizon must be >= 1")
    if horizon > 500:
        raise ApiError("horizon must be <= 500 for the local UI")
    return horizon


def _bool_value(raw_value: Any, default: bool = False) -> bool:
    if raw_value is None:
        return default
    if isinstance(raw_value, bool):
        return raw_value
    if isinstance(raw_value, str):
        return raw_value.strip().lower() in {"1", "true", "yes", "on"}
    return bool(raw_value)


def _float_value(payload: Mapping[str, Any], key: str, default: float) -> float:
    raw_value = payload.get(key, default)
    try:
        return float(raw_value)
    except (TypeError, ValueError) as exc:
        raise ApiError(f"{key} must be a number") from exc


def _int_value(payload: Mapping[str, Any], key: str, default: int) -> int:
    raw_value = payload.get(key, default)
    try:
        return int(raw_value)
    except (TypeError, ValueError) as exc:
        raise ApiError(f"{key} must be an integer") from exc


def _graph_payload(graph) -> dict[str, Any]:
    nodes = []
    for node_id, attrs in graph.nodes(data=True):
        nodes.append(
            {
                "id": str(node_id),
                "degree": int(graph.degree[node_id]),
                **_json_safe(dict(attrs)),
            }
        )
    edges = [{"source": str(source), "target": str(target)} for source, target in graph.edges()]
    compromised = sum(
        1
        for _, attrs in graph.nodes(data=True)
        if attrs.get("compromised_state") in {"user", "privileged"}
    )
    isolated = sum(1 for _, attrs in graph.nodes(data=True) if attrs.get("isolation_state"))
    detected = sum(1 for _, attrs in graph.nodes(data=True) if attrs.get("detection_state") == "detected")
    return {
        "nodes": nodes,
        "edges": edges,
        "stats": {
            "node_count": len(nodes),
            "edge_count": len(edges),
            "compromised_nodes": compromised,
            "isolated_nodes": isolated,
            "detected_nodes": detected,
        },
    }


def _scenario_summary(scenario) -> dict[str, Any]:
    vulnerabilities = sum(len(node.vulnerabilities) for node in scenario.nodes)
    isolated = sum(1 for node in scenario.nodes if node.isolation_state)
    compromised = sum(1 for node in scenario.nodes if node.compromised_state.value != "none")
    average_security = (
        sum(node.security_level for node in scenario.nodes) / max(1, len(scenario.nodes))
    )
    return {
        "scenario_id": scenario.metadata.scenario_id,
        "version": scenario.metadata.version,
        "node_count": len(scenario.nodes),
        "edge_count": len(scenario.edges),
        "vulnerabilities_count": vulnerabilities,
        "isolated_nodes": isolated,
        "initial_compromised_nodes": compromised,
        "average_security_level": round(average_security, 3),
    }


def _catalog_payload() -> list[dict[str, Any]]:
    entries = build_scenario_catalog()
    latest = {
        (entry.scenario_id, entry.source_group): entry.version
        for entry in select_latest_scenario_entries(entries)
    }
    payload = []
    for entry in entries:
        item = _json_safe(entry)
        item["is_latest_for_id"] = latest.get((entry.scenario_id, entry.source_group)) == entry.version
        payload.append(item)
    return payload


def _adaptive_config_from_payload(payload: Mapping[str, Any]) -> AdaptivePolicyConfig:
    return AdaptivePolicyConfig(
        planning_horizon=_int_value(payload, "planning_horizon", 3),
        discount_factor=_float_value(payload, "discount_factor", 0.85),
        exploration_bias=_float_value(payload, "exploration_bias", 0.15),
        max_compromised_projection=_int_value(payload, "max_compromised_projection", 128),
        reduced_observability=_bool_value(payload.get("reduced_observability"), False),
        enable_decoy=_bool_value(payload.get("enable_decoy"), False),
        enable_bluff=_bool_value(payload.get("enable_bluff"), False),
        deception_bias=_float_value(payload, "deception_bias", 1.0),
        decision_noise=_float_value(payload, "decision_noise", 0.0),
    )


def _actor_config(body: Mapping[str, Any], actor: str) -> AdaptivePolicyConfig:
    shared = body.get("adaptive_config") or {}
    actor_specific = body.get(f"{actor}_adaptive_config") or {}
    if not isinstance(shared, Mapping) or not isinstance(actor_specific, Mapping):
        raise ApiError("adaptive config values must be objects")
    merged = {**shared, **actor_specific}
    return _adaptive_config_from_payload(merged)


def _build_policy_registry(body: Mapping[str, Any]) -> tuple[PolicyRegistry, dict[str, str]]:
    red_policy = str(body.get("red_policy", "rule")).strip().lower()
    blue_policy = str(body.get("blue_policy", "rule")).strip().lower()
    allowed = {"rule", "adaptive"}
    if red_policy not in allowed or blue_policy not in allowed:
        raise ApiError("red_policy and blue_policy must be 'rule' or 'adaptive'")

    registry = PolicyRegistry()
    if red_policy == "adaptive":
        registry.register(AdaptivePlanningPolicy(actor=ActorType.RED, config=_actor_config(body, "red")))
    else:
        registry.register(RuleBasedRedPolicy())

    if blue_policy == "adaptive":
        registry.register(AdaptivePlanningPolicy(actor=ActorType.BLUE, config=_actor_config(body, "blue")))
    else:
        registry.register(RuleBasedBluePolicy())

    return registry, {"red_policy": red_policy, "blue_policy": blue_policy}


def _output_roots(body: Mapping[str, Any]) -> tuple[Path, Path, Path]:
    runs_root = _resolve_workspace_path(body.get("runs_root"), DEFAULT_RUNS_ROOT, allow_tmp=True)
    metrics_root = _resolve_workspace_path(body.get("metrics_root"), DEFAULT_METRICS_ROOT, allow_tmp=True)
    reports_root = _resolve_workspace_path(body.get("reports_root"), DEFAULT_REPORTS_ROOT, allow_tmp=True)
    return runs_root, metrics_root, reports_root


def _simulation_payload(result, baseline_metrics: dict[str, Any], artifacts: dict[str, str], metrics_file: str) -> dict[str, Any]:
    snapshots = [{"timestep": -1, "label": "initial", "graph": None}]
    for index, graph in enumerate(result.graph_snapshots):
        snapshots.append({"timestep": index, "label": f"turn {index + 1}", "graph": _graph_payload(graph)})

    timeline = []
    for entry in result.timesteps:
        timeline.append(
            {
                "timestep": entry.timestep,
                "red_action": _json_safe(entry.red_action_intent),
                "blue_action": _json_safe(entry.blue_action_intent),
                "metric_delta": _json_safe(entry.metric_delta),
                "state_diff": _json_safe(entry.post_state_diff),
                "pre_state_ref": entry.pre_state_ref,
                "post_state_ref": entry.post_state_ref,
            }
        )

    return {
        "metadata": _json_safe(result.metadata),
        "baseline_metrics": _json_safe(baseline_metrics),
        "artifacts": {key: _relative_path(value) for key, value in artifacts.items()},
        "baseline_metrics_file": _relative_path(metrics_file),
        "final_graph": _graph_payload(result.final_graph),
        "snapshots": snapshots,
        "timeline": timeline,
    }


def api_overview() -> dict[str, Any]:
    runs_root = PROJECT_ROOT / DEFAULT_RUNS_ROOT
    reports_root = PROJECT_ROOT / DEFAULT_REPORTS_ROOT
    metrics_root = PROJECT_ROOT / DEFAULT_METRICS_ROOT
    run_count = len(list(runs_root.rglob("run_metadata.json"))) if runs_root.exists() else 0
    report_count = (
        len([path for path in reports_root.rglob("*") if path.suffix in {".json", ".md"}])
        if reports_root.exists()
        else 0
    )
    metric_count = len(list(metrics_root.rglob("*.json"))) if metrics_root.exists() else 0
    return {
        "project_root": str(PROJECT_ROOT),
        "scenario_count": len(_catalog_payload()),
        "run_count": run_count,
        "metric_count": metric_count,
        "report_count": report_count,
        "capabilities": [
            "scenario_catalog",
            "scenario_validation",
            "rule_and_adaptive_simulation",
            "baseline_metrics",
            "replay_artifacts",
            "multi_seed_reports",
            "policy_experiment_matrix",
            "stress_test_suite",
            "ablation_report_package",
            "comparative_reports",
            "release_validation",
            "container_profiles",
        ],
    }


def api_scenarios() -> dict[str, Any]:
    return {"scenarios": _catalog_payload()}


def api_scenario_detail(raw_path: Any) -> dict[str, Any]:
    scenario_path = _resolve_workspace_path(raw_path, DEFAULT_SCENARIO_PATH, must_exist=True)
    scenario = load_scenario_file(scenario_path)
    graph = build_graph_from_scenario(scenario)
    raw_payload = json.loads(scenario_path.read_text(encoding="utf-8"))
    return {
        "path": _relative_path(scenario_path),
        "summary": _scenario_summary(scenario),
        "scenario": _json_safe(scenario),
        "raw": raw_payload,
        "graph": _graph_payload(graph),
    }


def api_validate_scenario(body: Mapping[str, Any]) -> dict[str, Any]:
    if body.get("path"):
        scenario = load_scenario_file(_resolve_workspace_path(body["path"], DEFAULT_SCENARIO_PATH, must_exist=True))
    else:
        payload = body.get("payload", body.get("scenario"))
        if not isinstance(payload, dict):
            raise ApiError("provide a scenario payload object or a path")
        scenario = validate_scenario_dict(payload)
    return {"ok": True, "summary": _scenario_summary(scenario), "scenario": _json_safe(scenario)}


def api_run_simulation(body: Mapping[str, Any]) -> dict[str, Any]:
    scenario_path = _resolve_workspace_path(body.get("scenario_path"), DEFAULT_SCENARIO_PATH, must_exist=True)
    seed = _parse_seeds(body.get("seed", body.get("seeds")), [20260329])[0]
    horizon = _parse_horizon(body.get("horizon"), 8)
    runs_root, metrics_root, _reports_root = _output_roots(body)

    scenario = load_scenario_file(scenario_path)
    graph = build_graph_from_scenario(scenario)
    registry, policy_info = _build_policy_registry(body)
    scenario_id = body.get("scenario_id") or scenario.metadata.scenario_id
    result = run_turn_based_simulation(
        graph,
        seed=seed,
        horizon=horizon,
        scenario_id=str(scenario_id),
        policy_registry=registry,
    )
    artifacts = write_run_artifacts(result, runs_root)
    metrics_file = write_baseline_metrics_artifact(result, metrics_root)
    baseline_metrics = compute_baseline_metrics(result)
    payload = _simulation_payload(result, baseline_metrics, artifacts, metrics_file)
    payload["scenario_path"] = _relative_path(scenario_path)
    payload["policies"] = policy_info
    initial_graph = build_graph_from_scenario(scenario)
    payload["snapshots"][0]["graph"] = _graph_payload(initial_graph)
    return payload


def _run_summary_from_dir(run_dir: Path) -> dict[str, Any]:
    try:
        bundle = load_run_artifact_bundle(run_dir)
        summary = dict(bundle["summary"])
        summary["run_dir"] = _relative_path(run_dir)
        return _json_safe(summary)
    except Exception as exc:
        metadata_path = run_dir / "run_metadata.json"
        metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
        return {
            "run_id": metadata.get("run_id", run_dir.name),
            "scenario_id": metadata.get("scenario_id", ""),
            "seed": metadata.get("seed"),
            "horizon": metadata.get("horizon"),
            "timestamp_utc": metadata.get("timestamp_utc", ""),
            "run_dir": _relative_path(run_dir),
            "load_error": str(exc),
        }


def _find_run_dir(run_id: str, runs_root: Path) -> Path:
    candidate = runs_root / run_id
    if (candidate / "run_metadata.json").exists():
        return candidate
    for metadata_path in runs_root.rglob("run_metadata.json"):
        if metadata_path.parent.name == run_id:
            return metadata_path.parent
    raise ApiError(f"run not found: {run_id}", HTTPStatus.NOT_FOUND)


def api_list_runs(raw_runs_root: Any = None) -> dict[str, Any]:
    runs_root = _resolve_workspace_path(raw_runs_root, DEFAULT_RUNS_ROOT, allow_tmp=True)
    if not runs_root.exists():
        return {"runs_root": _relative_path(runs_root), "runs": []}
    run_dirs = [path.parent for path in runs_root.rglob("run_metadata.json")]
    run_dirs.sort(key=lambda path: path.stat().st_mtime if path.exists() else 0, reverse=True)
    return {
        "runs_root": _relative_path(runs_root),
        "runs": [_run_summary_from_dir(run_dir) for run_dir in run_dirs[:250]],
    }


def api_run_detail(run_id: str | None = None, run_dir_raw: Any = None, raw_runs_root: Any = None) -> dict[str, Any]:
    runs_root = _resolve_workspace_path(raw_runs_root, DEFAULT_RUNS_ROOT, allow_tmp=True)
    if run_dir_raw:
        run_dir = _resolve_workspace_path(run_dir_raw, DEFAULT_RUNS_ROOT, allow_tmp=True, must_exist=True)
    elif run_id:
        run_dir = _find_run_dir(run_id, runs_root)
    else:
        raise ApiError("run_id or run_dir is required")
    bundle = load_run_artifact_bundle(run_dir)
    return {
        "run_dir": _relative_path(run_dir),
        "summary": _json_safe(bundle["summary"]),
        "metadata": _json_safe(bundle["metadata"]),
        "policy_metrics": _json_safe(bundle["policy_metrics"]),
        "replay_summary": _json_safe(bundle["replay_summary"]),
        "frames": _json_safe(bundle["frames"]),
    }


def _report_type_and_summary(payload: Mapping[str, Any]) -> tuple[str, dict[str, Any]]:
    if "aggregate" in payload:
        aggregate = payload["aggregate"]
        return "multi_seed", {
            "scenario_id": aggregate.get("scenario_id"),
            "seed_count": aggregate.get("seed_count"),
            "horizon": aggregate.get("horizon"),
            "final_compromised_mean": aggregate.get("final_compromised_mean"),
        }
    if "matrix_metadata" in payload:
        metadata = payload["matrix_metadata"]
        return "policy_matrix", {
            "scenario_id": metadata.get("scenario_id"),
            "seed_count": metadata.get("seed_count"),
            "condition_count": metadata.get("condition_count"),
            "include_ablations": metadata.get("include_ablations"),
        }
    if "batch_metadata" in payload:
        metadata = payload["batch_metadata"]
        return "policy_matrix_batch", {
            "scenario_count": metadata.get("scenario_count"),
            "seed_count": metadata.get("seed_count"),
            "horizon": metadata.get("horizon"),
        }
    if "suite_metadata" in payload:
        metadata = payload["suite_metadata"]
        return "stress_suite", {
            "profile_count": metadata.get("profile_count"),
            "profiles": metadata.get("profiles"),
        }
    if "template_metadata" in payload:
        metadata = payload["template_metadata"]
        return "ablation_template", {
            "scenario_id": metadata.get("scenario_id"),
            "condition_count": metadata.get("condition_count"),
            "table_count": metadata.get("table_count"),
        }
    if "manifest_id" in payload:
        return "artifact_manifest", {"manifest_id": payload.get("manifest_id")}
    if "all_gates_pass" in payload and "gates" in payload:
        return "release_readiness", {
            "all_gates_pass": payload.get("all_gates_pass"),
            "pass_count": payload.get("pass_count"),
            "fail_count": payload.get("fail_count"),
        }
    if "comparisons" in payload:
        return "comparative_report", _json_safe(payload.get("comparisons", {}))
    return "json", {}


def api_list_reports(raw_reports_root: Any = None) -> dict[str, Any]:
    reports_root = _resolve_workspace_path(raw_reports_root, DEFAULT_REPORTS_ROOT, allow_tmp=True)
    if not reports_root.exists():
        return {"reports_root": _relative_path(reports_root), "reports": []}

    reports = []
    for path in reports_root.rglob("*"):
        if not path.is_file() or path.name == "README.md" or path.suffix not in {".json", ".md"}:
            continue
        report_type = "markdown" if path.suffix == ".md" else "json"
        summary: dict[str, Any] = {}
        if path.suffix == ".json" and path.stat().st_size <= MAX_ARTIFACT_BYTES:
            try:
                payload = json.loads(path.read_text(encoding="utf-8"))
                if isinstance(payload, Mapping):
                    report_type, summary = _report_type_and_summary(payload)
            except Exception as exc:
                summary = {"load_error": str(exc)}
        reports.append(
            {
                "path": _relative_path(path),
                "name": path.name,
                "type": report_type,
                "size_bytes": path.stat().st_size,
                "modified": path.stat().st_mtime,
                "summary": summary,
            }
        )
    reports.sort(key=lambda item: item["modified"], reverse=True)
    return {"reports_root": _relative_path(reports_root), "reports": reports[:300]}


def api_artifact_file(raw_path: Any) -> dict[str, Any]:
    if raw_path in (None, ""):
        raise ApiError("path is required")
    path = _resolve_workspace_path(raw_path, "", allow_tmp=True, must_exist=True)
    if not path.is_file():
        raise ApiError("path is not a file")
    size = path.stat().st_size
    if size > MAX_ARTIFACT_BYTES:
        raise ApiError(f"artifact is too large for inline viewing ({size} bytes)")
    text = path.read_text(encoding="utf-8")
    if path.suffix == ".json":
        return {"path": _relative_path(path), "kind": "json", "payload": json.loads(text)}
    return {"path": _relative_path(path), "kind": "text", "text": text}


def api_run_multi_seed_report(body: Mapping[str, Any]) -> dict[str, Any]:
    scenario_path = _resolve_workspace_path(body.get("scenario_path"), DEFAULT_SCENARIO_PATH, must_exist=True)
    seeds = _parse_seeds(body.get("seeds"), [20260329, 20260330, 20260331])
    horizon = _parse_horizon(body.get("horizon"), 8)
    runs_root, metrics_root, reports_root = _output_roots(body)
    output = run_multi_seed_report(
        scenario_path=scenario_path,
        seeds=seeds,
        horizon=horizon,
        runs_root=runs_root,
        metrics_root=metrics_root,
        reports_root=reports_root,
    )
    return _json_safe({"report_file": output["report_file"], "report": output["report"]})


def _scenario_batch_from_body(body: Mapping[str, Any]) -> list[Path]:
    raw_batch = body.get("scenario_batch")
    if raw_batch in (None, ""):
        return []
    if isinstance(raw_batch, str):
        values = [value.strip() for value in raw_batch.split(",") if value.strip()]
    elif isinstance(raw_batch, (list, tuple)):
        values = [str(value).strip() for value in raw_batch if str(value).strip()]
    else:
        raise ApiError("scenario_batch must be a comma-separated string or list of paths")
    if not values:
        raise ApiError("scenario_batch cannot be empty")
    return [_resolve_workspace_path(value, DEFAULT_SCENARIO_PATH, must_exist=True) for value in values]


def api_run_policy_matrix(body: Mapping[str, Any]) -> dict[str, Any]:
    seeds = _parse_seeds(body.get("seeds"), [20260423, 20260424])
    horizon = _parse_horizon(body.get("horizon"), 2)
    include_ablations = _bool_value(body.get("include_ablations"), True)
    runs_root, metrics_root, reports_root = _output_roots(body)
    scenario_batch = _scenario_batch_from_body(body)
    if scenario_batch:
        output = run_policy_experiment_matrix_batch(
            scenario_paths=scenario_batch,
            seeds=seeds,
            horizon=horizon,
            runs_root=runs_root,
            metrics_root=metrics_root,
            reports_root=reports_root,
            include_ablations=include_ablations,
        )
    else:
        scenario_path = _resolve_workspace_path(body.get("scenario_path"), DEFAULT_SCENARIO_PATH, must_exist=True)
        output = run_policy_experiment_matrix(
            scenario_path=scenario_path,
            seeds=seeds,
            horizon=horizon,
            runs_root=runs_root,
            metrics_root=metrics_root,
            reports_root=reports_root,
            include_ablations=include_ablations,
        )
    return _json_safe({"report_file": output["report_file"], "report": output["report"]})


def api_run_stress_suite(body: Mapping[str, Any]) -> dict[str, Any]:
    seeds = _parse_seeds(body.get("seeds"), [20260423, 20260424])
    horizon = _parse_horizon(body.get("horizon"), 3)
    runs_root, metrics_root, reports_root = _output_roots(body)
    profiles = build_default_stress_test_configs(seeds=tuple(seeds), horizon=horizon)
    output = run_stress_test_suite(
        profiles=profiles,
        runs_root=runs_root,
        metrics_root=metrics_root,
        reports_root=reports_root,
    )
    return _json_safe({"report_file": output["report_file"], "report": output["report"]})


def api_run_ablation_report(body: Mapping[str, Any]) -> dict[str, Any]:
    scenario_path = _resolve_workspace_path(body.get("scenario_path"), DEFAULT_SCENARIO_PATH, must_exist=True)
    seeds = _parse_seeds(body.get("seeds"), [20260423, 20260424])
    horizon = _parse_horizon(body.get("horizon"), 2)
    runs_root, metrics_root, reports_root = _output_roots(body)
    output = run_ablation_report_package(
        scenario_path=scenario_path,
        seeds=seeds,
        horizon=horizon,
        runs_root=runs_root,
        metrics_root=metrics_root,
        reports_root=reports_root,
        include_ablations=_bool_value(body.get("include_ablations"), True),
        containerized=_bool_value(body.get("containerized"), False),
        container_image=str(body.get("container_image") or "python:3.12-slim"),
        container_working_directory=str(body.get("container_working_directory") or "/workspace/MARBTS"),
    )
    return _json_safe(output)


def api_generate_comparative_report(body: Mapping[str, Any]) -> dict[str, Any]:
    runs_root = _resolve_workspace_path(body.get("runs_root"), DEFAULT_RUNS_ROOT, allow_tmp=True)
    reports_root = _resolve_workspace_path(body.get("reports_root"), DEFAULT_REPORTS_ROOT, allow_tmp=True)
    figures_root = _resolve_workspace_path(body.get("figures_root"), DEFAULT_FIGURES_ROOT, allow_tmp=True)

    left_run_dir = body.get("left_run_dir")
    right_run_dir = body.get("right_run_dir")
    if not left_run_dir:
        left_run_dir = _find_run_dir(str(body.get("left_run_id", "")), runs_root)
    else:
        left_run_dir = _resolve_workspace_path(left_run_dir, DEFAULT_RUNS_ROOT, allow_tmp=True, must_exist=True)
    if not right_run_dir:
        right_run_dir = _find_run_dir(str(body.get("right_run_id", "")), runs_root)
    else:
        right_run_dir = _resolve_workspace_path(right_run_dir, DEFAULT_RUNS_ROOT, allow_tmp=True, must_exist=True)

    output = generate_comparative_report(
        left_run_dir=left_run_dir,
        right_run_dir=right_run_dir,
        reports_root=reports_root,
        figures_root=figures_root,
    )
    return _json_safe(output)


def api_presets() -> dict[str, Any]:
    presets = []
    for path in sorted((PROJECT_ROOT / "configs/experiments").glob("*.json")):
        try:
            preset = load_experiment_preset(path)
            presets.append({"path": _relative_path(path), "preset": _json_safe(preset)})
        except Exception as exc:
            presets.append({"path": _relative_path(path), "load_error": str(exc)})

    seed_bundles = []
    for path in sorted((PROJECT_ROOT / "configs/seeds").glob("*.json")):
        try:
            seed_bundles.append({"path": _relative_path(path), "bundle": _json_safe(load_seed_bundle(path))})
        except Exception as exc:
            seed_bundles.append({"path": _relative_path(path), "load_error": str(exc)})

    return {"presets": presets, "seed_bundles": seed_bundles}


def api_container_specs() -> dict[str, Any]:
    return {"specs": _json_safe(build_default_container_execution_specs())}


def api_container_profile(body: Mapping[str, Any]) -> dict[str, Any]:
    spec_id = str(body.get("spec_id") or "multi_seed_baseline")
    spec = get_container_execution_spec(spec_id)
    service_args = body.get("service_args") or []
    if isinstance(service_args, str):
        service_args = [arg for arg in service_args.split(" ") if arg]
    if not isinstance(service_args, list):
        raise ApiError("service_args must be a string or list")
    command = build_docker_compose_run_command(
        spec,
        compose_file=str(body.get("compose_file") or DEFAULT_COMPOSE_FILE),
        docker_binary=str(body.get("docker_binary") or "docker"),
        remove_container=not _bool_value(body.get("no_rm"), False),
        build_image=_bool_value(body.get("build_image"), False),
        service_args=service_args,
    )
    payload = {
        "spec": _json_safe(spec),
        "command": list(command),
        "command_text": " ".join(command),
        "dry_run": not _bool_value(body.get("execute"), False),
    }
    if _bool_value(body.get("execute"), False):
        completed = subprocess.run(command, capture_output=True, text=True, check=False)
        payload["returncode"] = completed.returncode
        payload["stdout"] = completed.stdout
        payload["stderr"] = completed.stderr
    return payload


def api_release_validation(body: Mapping[str, Any]) -> dict[str, Any]:
    reports_root = _resolve_workspace_path(body.get("reports_root"), DEFAULT_REPORTS_ROOT, allow_tmp=True)
    output = run_release_validation(root=PROJECT_ROOT, reports_root=reports_root)
    return _json_safe(output)


def _query_value(query: Mapping[str, list[str]], key: str, default: str | None = None) -> str | None:
    values = query.get(key)
    if not values:
        return default
    return values[0]


class MARBTSUIHandler(BaseHTTPRequestHandler):
    server_version = "MARBTSUI/0.1"

    def log_message(self, format: str, *args: Any) -> None:
        return

    def _read_json_body(self) -> dict[str, Any]:
        length = int(self.headers.get("Content-Length", "0") or "0")
        if length > MAX_BODY_BYTES:
            raise ApiError("request body is too large", HTTPStatus.REQUEST_ENTITY_TOO_LARGE)
        if length == 0:
            return {}
        raw_body = self.rfile.read(length).decode("utf-8")
        try:
            payload = json.loads(raw_body)
        except json.JSONDecodeError as exc:
            raise ApiError(f"invalid JSON body: {exc}") from exc
        if not isinstance(payload, dict):
            raise ApiError("JSON body must be an object")
        return payload

    def _send_json(self, payload: Any, status: HTTPStatus = HTTPStatus.OK) -> None:
        data = json.dumps(_json_safe(payload), indent=2, sort_keys=True).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def _send_text(self, text: str, status: HTTPStatus = HTTPStatus.OK, content_type: str = "text/plain") -> None:
        data = text.encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", f"{content_type}; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def _serve_static(self, raw_path: str) -> None:
        relative = unquote(raw_path.removeprefix("/static/"))
        path = (STATIC_ROOT / relative).resolve()
        if not _is_relative_to(path, STATIC_ROOT) or not path.is_file():
            self._send_text("not found", HTTPStatus.NOT_FOUND)
            return
        content_type = mimetypes.guess_type(path.name)[0] or "application/octet-stream"
        data = path.read_bytes()
        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self) -> None:
        parsed = urlparse(self.path)
        query = parse_qs(parsed.query)
        try:
            if parsed.path in {"", "/"}:
                self._serve_static("/static/index.html")
                return
            if parsed.path.startswith("/static/"):
                self._serve_static(parsed.path)
                return
            if parsed.path == "/api/overview":
                self._send_json(api_overview())
                return
            if parsed.path == "/api/scenarios":
                self._send_json(api_scenarios())
                return
            if parsed.path == "/api/scenario":
                self._send_json(api_scenario_detail(_query_value(query, "path")))
                return
            if parsed.path == "/api/presets":
                self._send_json(api_presets())
                return
            if parsed.path == "/api/runs":
                run_id = _query_value(query, "run_id")
                run_dir = _query_value(query, "run_dir")
                runs_root = _query_value(query, "runs_root")
                if run_id or run_dir:
                    self._send_json(api_run_detail(run_id, run_dir, runs_root))
                else:
                    self._send_json(api_list_runs(runs_root))
                return
            if parsed.path.startswith("/api/runs/"):
                run_id = unquote(parsed.path.removeprefix("/api/runs/"))
                self._send_json(api_run_detail(run_id=run_id, raw_runs_root=_query_value(query, "runs_root")))
                return
            if parsed.path == "/api/reports":
                self._send_json(api_list_reports(_query_value(query, "reports_root")))
                return
            if parsed.path == "/api/artifact":
                self._send_json(api_artifact_file(_query_value(query, "path")))
                return
            if parsed.path == "/api/container/specs":
                self._send_json(api_container_specs())
                return
            self._send_json({"error": "not found"}, HTTPStatus.NOT_FOUND)
        except ApiError as exc:
            self._send_json({"error": str(exc)}, exc.status)
        except Exception as exc:
            self._send_json({"error": str(exc)}, HTTPStatus.INTERNAL_SERVER_ERROR)

    def do_HEAD(self) -> None:
        parsed = urlparse(self.path)
        if parsed.path in {"", "/"}:
            path = (STATIC_ROOT / "index.html").resolve()
        elif parsed.path.startswith("/static/"):
            relative = unquote(parsed.path.removeprefix("/static/"))
            path = (STATIC_ROOT / relative).resolve()
        else:
            self.send_response(HTTPStatus.NOT_FOUND)
            self.end_headers()
            return

        if not _is_relative_to(path, STATIC_ROOT) or not path.is_file():
            self.send_response(HTTPStatus.NOT_FOUND)
            self.end_headers()
            return

        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", mimetypes.guess_type(path.name)[0] or "application/octet-stream")
        self.send_header("Content-Length", str(path.stat().st_size))
        self.end_headers()

    def do_POST(self) -> None:
        parsed = urlparse(self.path)
        try:
            body = self._read_json_body()
            routes = {
                "/api/scenarios/validate": api_validate_scenario,
                "/api/simulations/run": api_run_simulation,
                "/api/reports/multi-seed": api_run_multi_seed_report,
                "/api/reports/policy-matrix": api_run_policy_matrix,
                "/api/reports/stress-suite": api_run_stress_suite,
                "/api/reports/ablation": api_run_ablation_report,
                "/api/reports/compare": api_generate_comparative_report,
                "/api/container/profile": api_container_profile,
                "/api/release-validation": api_release_validation,
            }
            handler = routes.get(parsed.path)
            if handler is None:
                self._send_json({"error": "not found"}, HTTPStatus.NOT_FOUND)
                return
            self._send_json(handler(body))
        except ApiError as exc:
            self._send_json({"error": str(exc)}, exc.status)
        except Exception as exc:
            self._send_json({"error": str(exc)}, HTTPStatus.INTERNAL_SERVER_ERROR)


def serve(host: str = "127.0.0.1", port: int = 8765) -> None:
    server = ThreadingHTTPServer((host, port), MARBTSUIHandler)
    url = f"http://{host}:{server.server_port}"
    print(f"MARBTS_UI_READY url={url}")
    print(f"project_root={PROJECT_ROOT}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nMARBTS_UI_STOPPED")
    finally:
        server.server_close()


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Run the local MARBTS web UI.")
    parser.add_argument("--host", default="127.0.0.1", help="Host interface to bind.")
    parser.add_argument("--port", type=int, default=8765, help="Port to bind.")
    args = parser.parse_args(argv)
    serve(host=args.host, port=args.port)


if __name__ == "__main__":
    main()
