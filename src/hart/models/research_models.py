from __future__ import annotations

from dataclasses import dataclass, field
from typing import Mapping


@dataclass(frozen=True)
class DeceptionEvent:
    event_type: str
    node_id: str
    actor: str
    timestep: int
    description: str
    metadata: Mapping[str, object] = field(default_factory=dict)


@dataclass(frozen=True)
class ContainerExecutionConfig:
    image_name: str
    workdir: str
    entrypoint: str
    requirements_file: str


@dataclass(frozen=True)
class ResearchArtifactManifest:
    manifest_id: str
    generated_at_utc: str
    report_files: tuple[str, ...]
    config_files: tuple[str, ...]
    scenario_catalog_path: str
    notes: tuple[str, ...] = ()


@dataclass(frozen=True)
class PublicationMetricTable:
    table_id: str
    scenario_id: str
    rows: tuple[Mapping[str, object], ...]


@dataclass(frozen=True)
class AblationMatrixCondition:
    condition_id: str
    red_mode: str
    blue_mode: str
    feature_flags: Mapping[str, bool] = field(default_factory=dict)


@dataclass(frozen=True)
class AblationMatrix:
    matrix_id: str
    scenario_id: str
    seeds: tuple[int, ...]
    horizon: int
    planner_depth: int
    conditions: tuple[AblationMatrixCondition, ...]
