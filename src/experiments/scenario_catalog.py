from __future__ import annotations

import json
from pathlib import Path

from hart.models import ScenarioCatalogEntry
from schemas.scenario import load_scenario_file


def load_scenario_catalog(catalog_path: str | Path) -> tuple[ScenarioCatalogEntry, ...]:
    path = Path(catalog_path)
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("scenario catalog root must be an object")

    entries_obj = payload.get("entries")
    if not isinstance(entries_obj, list):
        raise ValueError("scenario catalog must contain an 'entries' list")

    entries: list[ScenarioCatalogEntry] = []
    seen_ids: set[tuple[str, str]] = set()
    for entry_obj in entries_obj:
        if not isinstance(entry_obj, dict):
            raise ValueError("scenario catalog entries must be objects")
        entry = ScenarioCatalogEntry(
            scenario_id=str(entry_obj["scenario_id"]),
            version=str(entry_obj["version"]),
            path=str(entry_obj["path"]),
            tags=tuple(str(tag) for tag in entry_obj.get("tags", [])),
            topology_complexity=str(entry_obj.get("topology_complexity", "unknown")),
            vulnerability_density=str(entry_obj.get("vulnerability_density", "unknown")),
            defense_posture=str(entry_obj.get("defense_posture", "unknown")),
        )
        key = (entry.scenario_id, entry.version)
        if key in seen_ids:
            raise ValueError(f"duplicate scenario catalog entry for scenario_id={entry.scenario_id!r} version={entry.version!r}")
        seen_ids.add(key)
        entries.append(entry)

    return tuple(entries)


def validate_scenario_catalog(catalog_path: str | Path) -> tuple[ScenarioCatalogEntry, ...]:
    catalog_entries = load_scenario_catalog(catalog_path)
    base_dir = Path(catalog_path).parent

    for entry in catalog_entries:
        scenario_path = (base_dir / entry.path).resolve()
        scenario = load_scenario_file(scenario_path)
        if scenario.metadata.scenario_id != entry.scenario_id:
            raise ValueError(
                f"catalog entry scenario_id mismatch for {entry.path}: expected {entry.scenario_id!r}, got {scenario.metadata.scenario_id!r}"
            )
        if scenario.metadata.version != entry.version:
            raise ValueError(
                f"catalog entry version mismatch for {entry.path}: expected {entry.version!r}, got {scenario.metadata.version!r}"
            )

    return catalog_entries


def resolve_catalog_scenario_path(catalog_path: str | Path, scenario_id: str, version: str | None = None) -> Path:
    entries = validate_scenario_catalog(catalog_path)
    candidates = [entry for entry in entries if entry.scenario_id == scenario_id]
    if version is not None:
        candidates = [entry for entry in candidates if entry.version == version]
    if not candidates:
        raise ValueError(f"scenario {scenario_id!r} not found in catalog")

    selected = sorted(candidates, key=lambda item: item.version)[-1]
    return (Path(catalog_path).parent / selected.path).resolve()
