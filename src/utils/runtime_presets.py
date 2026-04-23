from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Mapping, Sequence

from hart.models import ExperimentPreset, RuntimeConfig, SeedBundle


def _load_json_mapping(path: str | Path) -> Mapping[str, Any]:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(payload, Mapping):
        raise ValueError(f"config payload must be an object: {path}")
    return payload


def _parse_int_tuple(raw_value: Any, *, field_name: str) -> tuple[int, ...]:
    if raw_value is None:
        return ()
    if isinstance(raw_value, str):
        tokens = [token.strip() for token in raw_value.split(",") if token.strip()]
        try:
            return tuple(int(token) for token in tokens)
        except ValueError as exc:
            raise ValueError(f"{field_name} must be a comma-separated list of integers") from exc
    if isinstance(raw_value, Sequence) and not isinstance(raw_value, (str, bytes, bytearray)):
        try:
            return tuple(int(item) for item in raw_value)
        except (TypeError, ValueError) as exc:
            raise ValueError(f"{field_name} must be a sequence of integers") from exc
    raise ValueError(f"{field_name} must be a list, tuple, or comma-separated string")


def _parse_str_tuple(raw_value: Any, *, field_name: str) -> tuple[str, ...]:
    if raw_value is None:
        return ()
    if isinstance(raw_value, str):
        values = tuple(item.strip() for item in raw_value.split(",") if item.strip())
        if not values:
            raise ValueError(f"{field_name} must include at least one path")
        return values
    if isinstance(raw_value, Sequence) and not isinstance(raw_value, (str, bytes, bytearray)):
        values = tuple(str(item).strip() for item in raw_value if str(item).strip())
        if not values:
            raise ValueError(f"{field_name} must include at least one path")
        return values
    raise ValueError(f"{field_name} must be a sequence of strings")


def _parse_optional_str(raw_value: Any, *, field_name: str) -> str | None:
    if raw_value is None:
        return None
    value = str(raw_value).strip()
    if not value:
        raise ValueError(f"{field_name} cannot be empty")
    return value


def load_seed_bundle(path: str | Path) -> SeedBundle:
    payload = _load_json_mapping(path)
    return SeedBundle(
        schema_version=str(payload.get("schema_version", "2026-04-24.seed_bundle.v1")),
        bundle_id=str(payload.get("bundle_id", "")).strip(),
        description=str(payload.get("description", "")).strip(),
        seeds=_parse_int_tuple(payload.get("seeds"), field_name="seeds"),
    )


def load_experiment_preset(path: str | Path) -> ExperimentPreset:
    preset_path = Path(path)
    payload = _load_json_mapping(preset_path)

    runtime_payload = payload.get("runtime", {})
    if not isinstance(runtime_payload, Mapping):
        raise ValueError("runtime must be an object")

    runtime_seeds = _parse_int_tuple(runtime_payload.get("seeds"), field_name="runtime.seeds")
    seed_bundle_raw = payload.get("seed_bundle")
    seed_bundle_path = _parse_optional_str(seed_bundle_raw, field_name="seed_bundle")
    seed_bundle = None
    if seed_bundle_path is not None:
        resolved_bundle_path = Path(seed_bundle_path)
        if not resolved_bundle_path.is_absolute():
            resolved_bundle_path = preset_path.parent / resolved_bundle_path
        seed_bundle = load_seed_bundle(resolved_bundle_path)

    seeds = runtime_seeds or (seed_bundle.seeds if seed_bundle is not None else ())

    return ExperimentPreset(
        schema_version=str(payload.get("schema_version", "2026-04-24.runtime_preset.v1")),
        preset_id=str(payload.get("preset_id", "")).strip(),
        description=str(payload.get("description", "")).strip(),
        runtime=RuntimeConfig(
            scenario_path=_parse_optional_str(runtime_payload.get("scenario_path"), field_name="runtime.scenario_path"),
            scenario_batch=_parse_str_tuple(runtime_payload.get("scenario_batch"), field_name="runtime.scenario_batch")
            if runtime_payload.get("scenario_batch") is not None
            else (),
            seeds=seeds,
            horizon=int(runtime_payload.get("horizon", 1)),
            runs_root=str(runtime_payload.get("runs_root", "artifacts/runs")),
            metrics_root=str(runtime_payload.get("metrics_root", "artifacts/metrics")),
            reports_root=str(runtime_payload.get("reports_root", "artifacts/reports")),
        ),
        seed_bundle=seed_bundle.bundle_id if seed_bundle is not None else None,
        include_ablations=(
            bool(payload["include_ablations"]) if payload.get("include_ablations") is not None else None
        ),
        containerized=bool(payload.get("containerized", False)),
        container_image=str(payload.get("container_image", "python:3.12-slim")),
        container_working_directory=str(payload.get("container_working_directory", "/workspace/MARBTS")),
    )
