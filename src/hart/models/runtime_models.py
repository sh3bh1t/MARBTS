from __future__ import annotations

from dataclasses import dataclass, field
from typing import Mapping


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


@dataclass(frozen=True)
class ContainerExecutionSpec:
    spec_id: str
    service_name: str
    compose_profile: str
    description: str
    marbts_subcommand: str
    preset_config_path: str
    additional_args: tuple[str, ...] = field(default_factory=tuple)
    image: str = "marbts:phase6-local"
    working_directory: str = "/workspace/MARBTS"
    environment: Mapping[str, str] = field(default_factory=lambda: {"PYTHONPATH": "src"})

    def __post_init__(self) -> None:
        if not self.spec_id:
            raise ValueError("spec_id must be a non-empty string")
        if not self.service_name:
            raise ValueError("service_name must be a non-empty string")
        if not self.compose_profile:
            raise ValueError("compose_profile must be a non-empty string")
        if not self.description:
            raise ValueError("description must be a non-empty string")
        if not self.marbts_subcommand:
            raise ValueError("marbts_subcommand must be a non-empty string")
        if not self.preset_config_path:
            raise ValueError("preset_config_path must be a non-empty string")
        if any(not arg.strip() for arg in self.additional_args):
            raise ValueError("additional_args cannot contain empty entries")
        if not self.image:
            raise ValueError("image must be a non-empty string")
        if not self.working_directory:
            raise ValueError("working_directory must be a non-empty string")
        if any(not key.strip() for key in self.environment):
            raise ValueError("environment keys must be non-empty strings")
        if any(not str(value).strip() for value in self.environment.values()):
            raise ValueError("environment values must be non-empty strings")

    @property
    def marbts_command(self) -> tuple[str, ...]:
        return (
            self.marbts_subcommand,
            "--config",
            self.preset_config_path,
            *self.additional_args,
        )


@dataclass(frozen=True)
class ReleaseGate:
    gate_id: str
    description: str
    status: str  # "pass" | "fail"
    evidence: str = ""
    failure_detail: str = ""

    def __post_init__(self) -> None:
        if not self.gate_id:
            raise ValueError("gate_id must be a non-empty string")
        if not self.description:
            raise ValueError("description must be a non-empty string")
        if self.status not in ("pass", "fail"):
            raise ValueError(f"status must be 'pass' or 'fail', got {self.status!r}")


@dataclass(frozen=True)
class ReleaseReadinessReport:
    schema_version: str
    timestamp_utc: str
    all_gates_pass: bool
    gate_count: int
    pass_count: int
    fail_count: int
    gates: tuple[ReleaseGate, ...]

    def __post_init__(self) -> None:
        if not self.schema_version:
            raise ValueError("schema_version must be a non-empty string")
        if not self.timestamp_utc:
            raise ValueError("timestamp_utc must be a non-empty string")
        if self.gate_count < 0:
            raise ValueError("gate_count must be >= 0")
        if self.pass_count < 0:
            raise ValueError("pass_count must be >= 0")
        if self.fail_count < 0:
            raise ValueError("fail_count must be >= 0")
        if self.pass_count + self.fail_count != self.gate_count:
            raise ValueError("pass_count + fail_count must equal gate_count")
