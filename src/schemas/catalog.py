from __future__ import annotations

import re
from pathlib import Path
from typing import Iterable, Mapping

from packaging.version import InvalidVersion, Version

from hart.enums import DefensePosture, TopologyComplexity, VulnerabilityDensity
from hart.models import ScenarioCatalogEntry, ScenarioConfig, ScenarioTaxonomy

from .scenario import load_scenario_file


_SEMVER_PATTERN = re.compile(r"^(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)$")
_DEFAULT_SCENARIO_ROOTS: dict[str, str] = {
    "baselines": "scenarios/baselines",
    "library": "scenarios/library",
}
_DEFAULT_EXCLUDE_PREFIXES = ("invalid_",)


def _parse_semantic_version(version: str) -> Version:
    if not _SEMVER_PATTERN.fullmatch(version):
        raise ValueError(
            f"scenario metadata.version '{version}' must follow semantic version format 'MAJOR.MINOR.PATCH'"
        )

    try:
        return Version(version)
    except InvalidVersion as exc:
        raise ValueError(f"scenario metadata.version '{version}' is not a valid semantic version") from exc


def _classify_topology_complexity(*, node_count: int, edge_count: int) -> TopologyComplexity:
    edge_to_node_ratio = edge_count / max(1, node_count)

    if node_count >= 10 or edge_to_node_ratio >= 2.0:
        return TopologyComplexity.COMPLEX
    if node_count >= 5 or edge_to_node_ratio >= 1.2:
        return TopologyComplexity.MODERATE
    return TopologyComplexity.SIMPLE


def _classify_vulnerability_density(*, vulnerabilities_count: int, node_count: int) -> VulnerabilityDensity:
    vulnerabilities_per_node = vulnerabilities_count / max(1, node_count)

    if vulnerabilities_per_node >= 2.5:
        return VulnerabilityDensity.HIGH
    if vulnerabilities_per_node >= 1.0:
        return VulnerabilityDensity.MEDIUM
    return VulnerabilityDensity.LOW


def _classify_defense_posture(*, average_security_level: float, isolated_node_ratio: float) -> DefensePosture:
    if average_security_level >= 4.0 and isolated_node_ratio >= 0.2:
        return DefensePosture.HARDENED
    if average_security_level >= 3.0:
        return DefensePosture.BALANCED
    return DefensePosture.PERMISSIVE


def _build_taxonomy(scenario: ScenarioConfig) -> ScenarioTaxonomy:
    node_count = len(scenario.nodes)
    edge_count = len(scenario.edges)
    vulnerabilities_count = sum(len(node.vulnerabilities) for node in scenario.nodes)
    isolated_nodes = sum(1 for node in scenario.nodes if node.isolation_state)
    average_security_level = (
        sum(node.security_level for node in scenario.nodes) / max(1, node_count)
    )

    return ScenarioTaxonomy(
        topology_complexity=_classify_topology_complexity(node_count=node_count, edge_count=edge_count),
        vulnerability_density=_classify_vulnerability_density(
            vulnerabilities_count=vulnerabilities_count,
            node_count=node_count,
        ),
        defense_posture=_classify_defense_posture(
            average_security_level=average_security_level,
            isolated_node_ratio=isolated_nodes / max(1, node_count),
        ),
    )


def _build_catalog_entry(*, scenario_path: Path, source_group: str) -> ScenarioCatalogEntry:
    scenario = load_scenario_file(scenario_path)
    _parse_semantic_version(scenario.metadata.version)

    node_count = len(scenario.nodes)
    edge_count = len(scenario.edges)
    vulnerabilities_count = sum(len(node.vulnerabilities) for node in scenario.nodes)
    average_security_level = round(
        sum(node.security_level for node in scenario.nodes) / max(1, node_count),
        3,
    )
    taxonomy = _build_taxonomy(scenario)

    return ScenarioCatalogEntry(
        scenario_id=scenario.metadata.scenario_id,
        version=scenario.metadata.version,
        source_group=source_group,
        scenario_path=scenario_path.as_posix(),
        node_count=node_count,
        edge_count=edge_count,
        vulnerabilities_count=vulnerabilities_count,
        average_security_level=average_security_level,
        taxonomy=taxonomy,
        tags=(
            f"topology:{taxonomy.topology_complexity.value}",
            f"vulnerability_density:{taxonomy.vulnerability_density.value}",
            f"defense_posture:{taxonomy.defense_posture.value}",
        ),
    )


def build_scenario_catalog(
    *,
    scenario_roots: Mapping[str, str | Path] | None = None,
    exclude_file_prefixes: tuple[str, ...] = _DEFAULT_EXCLUDE_PREFIXES,
) -> tuple[ScenarioCatalogEntry, ...]:
    roots = scenario_roots or _DEFAULT_SCENARIO_ROOTS
    entries: list[ScenarioCatalogEntry] = []

    for source_group, root in roots.items():
        root_path = Path(root)
        if not root_path.exists():
            raise ValueError(f"scenario root does not exist: {root_path}")

        for scenario_path in sorted(root_path.glob("*.json")):
            if scenario_path.name.startswith(exclude_file_prefixes):
                continue
            entries.append(_build_catalog_entry(scenario_path=scenario_path, source_group=source_group))

    entries.sort(key=lambda entry: (entry.scenario_id, _parse_semantic_version(entry.version), entry.source_group))
    return tuple(entries)


def select_latest_scenario_entries(entries: Iterable[ScenarioCatalogEntry]) -> tuple[ScenarioCatalogEntry, ...]:
    latest_by_id: dict[str, ScenarioCatalogEntry] = {}

    for entry in entries:
        current = latest_by_id.get(entry.scenario_id)
        if current is None:
            latest_by_id[entry.scenario_id] = entry
            continue

        if _parse_semantic_version(entry.version) > _parse_semantic_version(current.version):
            latest_by_id[entry.scenario_id] = entry

    return tuple(latest_by_id[scenario_id] for scenario_id in sorted(latest_by_id.keys()))