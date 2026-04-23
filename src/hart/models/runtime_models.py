from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class SeedBundle:
    schema_version: str = "2026-04-24.seed_bundle.v1"
    bundle_id: str = ""
    description: str = ""
    seeds: tuple[int, ...] = field(default_factory=tuple)

    def __post_init__(self) -> None:
        if not self.bundle_id:
            raise ValueError("bundle_id must be a non-empty string")
        if not self.seeds:
            raise ValueError("seeds cannot be empty")
        if any(seed < 0 for seed in self.seeds):
            raise ValueError("all seeds must be >= 0")


@dataclass(frozen=True)
class RuntimeConfig:
    scenario_path: str | None = None
    scenario_batch: tuple[str, ...] = field(default_factory=tuple)
    seeds: tuple[int, ...] = field(default_factory=tuple)
    horizon: int = 1
    runs_root: str = "artifacts/runs"
    metrics_root: str = "artifacts/metrics"
    reports_root: str = "artifacts/reports"

    def __post_init__(self) -> None:
        if self.horizon < 1:
            raise ValueError("horizon must be >= 1")
        if any(seed < 0 for seed in self.seeds):
            raise ValueError("all seeds must be >= 0")
        if any(not item.strip() for item in self.scenario_batch):
            raise ValueError("scenario_batch paths must be non-empty strings")


@dataclass(frozen=True)
class ExperimentPreset:
    schema_version: str = "2026-04-24.runtime_preset.v1"
    preset_id: str = ""
    description: str = ""
    runtime: RuntimeConfig = field(default_factory=RuntimeConfig)
    seed_bundle: str | None = None
    include_ablations: bool | None = None
    containerized: bool = False
    container_image: str = "python:3.12-slim"
    container_working_directory: str = "/workspace/MARBTS"

    def __post_init__(self) -> None:
        if not self.preset_id:
            raise ValueError("preset_id must be a non-empty string")
        if not self.container_image:
            raise ValueError("container_image must be a non-empty string")
        if not self.container_working_directory:
            raise ValueError("container_working_directory must be a non-empty string")
