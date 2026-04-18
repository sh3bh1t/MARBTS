from pathlib import Path

from experiments.scenario_catalog import resolve_catalog_scenario_path, validate_scenario_catalog


def test_validate_scenario_catalog_and_resolve_paths() -> None:
    catalog_path = Path("scenarios/library/catalog.json")
    entries = validate_scenario_catalog(catalog_path)

    assert len(entries) >= 3
    resolved = resolve_catalog_scenario_path(catalog_path, "phase5-large-mesh")
    assert resolved.name == "phase5_large_mesh_v1.json"
