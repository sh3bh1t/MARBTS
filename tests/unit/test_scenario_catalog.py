from __future__ import annotations

import json
from pathlib import Path

import pytest

from hart.enums import DefensePosture, TopologyComplexity, VulnerabilityDensity
from schemas.catalog import build_scenario_catalog, select_latest_scenario_entries


def _scenario_payload(*, scenario_id: str, version: str) -> dict:
    return {
        "metadata": {"scenario_id": scenario_id, "version": version},
        "nodes": [
            {
                "node_id": "srv-1",
                "node_type": "server",
                "services": ["ssh"],
                "vulnerabilities": ["cve-sim-001"],
                "security_level": 3,
                "compromised_state": "none",
                "detection_state": "undetected",
                "isolation_state": False,
            },
            {
                "node_id": "db-1",
                "node_type": "database",
                "services": ["postgres"],
                "vulnerabilities": ["cve-sim-010"],
                "security_level": 4,
                "compromised_state": "none",
                "detection_state": "undetected",
                "isolation_state": False,
            },
        ],
        "edges": [{"source": "srv-1", "target": "db-1"}],
    }


def _write_scenario(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def test_build_scenario_catalog_loads_current_library_and_taxonomy() -> None:
    entries = build_scenario_catalog()

    scenario_ids = {entry.scenario_id for entry in entries}
    assert "baseline-small" in scenario_ids
    assert "rule-baseline" in scenario_ids
    assert "containment-stress" in scenario_ids
    assert "scale-chain-6" in scenario_ids

    assert all(not Path(entry.scenario_path).name.startswith("invalid_") for entry in entries)

    for entry in entries:
        assert entry.version in {"1.0.0", "2.0.0"}
        assert isinstance(entry.node_count, int)
        assert isinstance(entry.edge_count, int)
        assert isinstance(entry.vulnerabilities_count, int)
        assert isinstance(entry.average_security_level, float)
        assert entry.tags
        assert entry.taxonomy.topology_complexity in TopologyComplexity
        assert entry.taxonomy.vulnerability_density in VulnerabilityDensity
        assert entry.taxonomy.defense_posture in DefensePosture


def test_build_scenario_catalog_rejects_invalid_semantic_version(tmp_path: Path) -> None:
    scenario_root = tmp_path / "catalog"
    _write_scenario(
        scenario_root / "bad_semver.json",
        _scenario_payload(scenario_id="invalid-semver", version="1.0"),
    )

    with pytest.raises(ValueError, match="semantic version format"):
        build_scenario_catalog(scenario_roots={"tmp": scenario_root})


def test_select_latest_scenario_entries_uses_semantic_version_ordering(tmp_path: Path) -> None:
    scenario_root = tmp_path / "catalog"
    _write_scenario(
        scenario_root / "alpha_120.json",
        _scenario_payload(scenario_id="alpha", version="1.2.0"),
    )
    _write_scenario(
        scenario_root / "alpha_1100.json",
        _scenario_payload(scenario_id="alpha", version="1.10.0"),
    )
    _write_scenario(
        scenario_root / "beta_100.json",
        _scenario_payload(scenario_id="beta", version="1.0.0"),
    )

    entries = build_scenario_catalog(scenario_roots={"tmp": scenario_root})
    latest = select_latest_scenario_entries(entries)
    latest_by_id = {entry.scenario_id: entry for entry in latest}

    assert set(latest_by_id.keys()) == {"alpha", "beta"}
    assert latest_by_id["alpha"].version == "1.10.0"
    assert latest_by_id["beta"].version == "1.0.0"