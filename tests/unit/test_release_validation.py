from __future__ import annotations

import json
from pathlib import Path

import pytest

from utils.release_validation import (
    EXPECTED_ENTRY_POINTS,
    EXPECTED_PHASE6_TEST_FILES,
    EXPECTED_PRESET_FILES,
    EXPECTED_SCRIPTS,
    EXPECTED_SEED_BUNDLE_FILES,
    README_RELEASE_MARKER,
    SCHEMA_VERSION,
    run_release_validation,
)


# ---------------------------------------------------------------------------
# Test fixture helpers
# ---------------------------------------------------------------------------


def _make_minimal_valid_root(tmp_path: Path) -> Path:
    """Build a minimal fake project root that passes all release gates."""

    # --- pyproject.toml with all required entry points ---
    entry_point_lines = "\n".join(
        f'{ep.rstrip(" =")} = "fake:main"' for ep in EXPECTED_ENTRY_POINTS
    )
    (tmp_path / "pyproject.toml").write_text(
        f'[project]\nversion = "0.6.0"\n\n[project.scripts]\n{entry_point_lines}\n',
        encoding="utf-8",
    )

    # --- Config preset JSON files ---
    for preset_path in EXPECTED_PRESET_FILES:
        full = tmp_path / preset_path
        full.parent.mkdir(parents=True, exist_ok=True)
        full.write_text(
            json.dumps(
                {
                    "schema_version": "2026-04-24.runtime_preset.v1",
                    "preset_id": Path(preset_path).stem,
                    "runtime": {
                        "scenario_path": "scenarios/baselines/rule_baseline.json",
                        "horizon": 2,
                        "seeds": [20260329],
                        "runs_root": "artifacts/runs",
                        "metrics_root": "artifacts/metrics",
                        "reports_root": "artifacts/reports",
                    },
                }
            ),
            encoding="utf-8",
        )

    # --- Seed bundle JSON files ---
    for bundle_path in EXPECTED_SEED_BUNDLE_FILES:
        full = tmp_path / bundle_path
        full.parent.mkdir(parents=True, exist_ok=True)
        full.write_text(
            json.dumps(
                {
                    "schema_version": "2026-04-24.seed_bundle.v1",
                    "bundle_id": Path(bundle_path).stem,
                    "seeds": [20260329, 20260330],
                }
            ),
            encoding="utf-8",
        )

    # --- Docker assets ---
    (tmp_path / "docker").mkdir(exist_ok=True)
    (tmp_path / "docker" / "Dockerfile").write_text(
        'FROM python:3.12-slim\nENTRYPOINT ["marbts"]\n', encoding="utf-8"
    )
    (tmp_path / "docker" / "docker-compose.yml").write_text(
        "services:\n  marbts-shell:\n    image: marbts\n", encoding="utf-8"
    )

    # --- Notebook files ---
    (tmp_path / "notebooks").mkdir(exist_ok=True)
    notebook_template = json.dumps(
        {
            "nbformat": 4,
            "nbformat_minor": 5,
            "metadata": {
                "marbts_workflow": {
                    "phase": "6",
                    "workflow_id": "fake_workflow",
                    "generator_commands": ["python scripts/run_multi_seed_report.py"],
                    "required_reports": ["report.json"],
                }
            },
            "cells": [
                {
                    "cell_type": "code",
                    "source": [
                        "RUN_GENERATORS = False\n",
                        "# scripts/run_multi_seed_report.py\n",
                    ],
                    "metadata": {},
                    "outputs": [],
                    "execution_count": None,
                }
            ],
        }
    )
    from utils.release_validation import EXPECTED_NOTEBOOK_FILES as NB_FILES

    for nb_path_str in NB_FILES:
        (tmp_path / nb_path_str).write_text(notebook_template, encoding="utf-8")

    # --- Scripts ---
    (tmp_path / "scripts").mkdir(exist_ok=True)
    for script_path in EXPECTED_SCRIPTS:
        (tmp_path / script_path).write_text("# stub\n", encoding="utf-8")

    # --- Test files ---
    (tmp_path / "tests" / "unit").mkdir(parents=True, exist_ok=True)
    (tmp_path / "tests" / "integration").mkdir(parents=True, exist_ok=True)
    for test_path in EXPECTED_PHASE6_TEST_FILES:
        (tmp_path / test_path).write_text("# test stub\n", encoding="utf-8")

    # --- README with release validation marker ---
    (tmp_path / "README.md").write_text(
        f"# MARBTS\n\nRun validation: python scripts/{README_RELEASE_MARKER}.py\n",
        encoding="utf-8",
    )

    return tmp_path


# ---------------------------------------------------------------------------
# Core validation tests
# ---------------------------------------------------------------------------


def test_all_gates_pass_on_fully_valid_root(tmp_path: Path) -> None:
    root = _make_minimal_valid_root(tmp_path)
    result = run_release_validation(root=root)
    report = result["report"]

    assert report.schema_version == SCHEMA_VERSION
    assert report.all_gates_pass is True
    assert report.fail_count == 0
    assert report.pass_count == report.gate_count
    assert len(report.gates) == report.gate_count
    assert result["report_file"] is None


def test_packaging_gate_fails_when_entry_point_missing(tmp_path: Path) -> None:
    root = _make_minimal_valid_root(tmp_path)
    # Overwrite pyproject.toml with only the base marbts entry — release-validation is absent
    (root / "pyproject.toml").write_text(
        '[project]\nversion = "0.6.0"\n\n[project.scripts]\nmarbts = "fake:main"\n',
        encoding="utf-8",
    )
    result = run_release_validation(root=root)
    report = result["report"]

    assert report.all_gates_pass is False
    packaging_gate = next(g for g in report.gates if g.gate_id == "packaging")
    assert packaging_gate.status == "fail"
    assert "missing entry points" in packaging_gate.failure_detail


def test_config_presets_gate_fails_when_file_missing(tmp_path: Path) -> None:
    root = _make_minimal_valid_root(tmp_path)
    (root / EXPECTED_PRESET_FILES[0]).unlink()

    result = run_release_validation(root=root)
    report = result["report"]

    assert report.all_gates_pass is False
    gate = next(g for g in report.gates if g.gate_id == "config_presets")
    assert gate.status == "fail"
    assert "missing preset files" in gate.failure_detail


def test_seed_bundles_gate_fails_when_file_missing(tmp_path: Path) -> None:
    root = _make_minimal_valid_root(tmp_path)
    (root / EXPECTED_SEED_BUNDLE_FILES[0]).unlink()

    result = run_release_validation(root=root)
    report = result["report"]

    assert report.all_gates_pass is False
    gate = next(g for g in report.gates if g.gate_id == "seed_bundles")
    assert gate.status == "fail"
    assert "missing seed bundle files" in gate.failure_detail


def test_docker_assets_gate_fails_when_dockerfile_missing(tmp_path: Path) -> None:
    root = _make_minimal_valid_root(tmp_path)
    (root / "docker" / "Dockerfile").unlink()

    result = run_release_validation(root=root)
    report = result["report"]

    assert report.all_gates_pass is False
    gate = next(g for g in report.gates if g.gate_id == "docker_assets")
    assert gate.status == "fail"


def test_notebook_assets_gate_fails_when_notebook_missing_workflow_field(tmp_path: Path) -> None:
    from utils.release_validation import EXPECTED_NOTEBOOK_FILES as NB_FILES

    root = _make_minimal_valid_root(tmp_path)
    bad_nb = json.dumps(
        {
            "nbformat": 4,
            "nbformat_minor": 5,
            "metadata": {"marbts_workflow": {"phase": "6"}},  # missing other required fields
            "cells": [
                {
                    "cell_type": "code",
                    "source": ["RUN_GENERATORS = False\n# scripts/run_multi_seed_report.py\n"],
                    "metadata": {},
                    "outputs": [],
                    "execution_count": None,
                }
            ],
        }
    )
    (root / NB_FILES[0]).write_text(bad_nb, encoding="utf-8")

    result = run_release_validation(root=root)
    report = result["report"]

    assert report.all_gates_pass is False
    gate = next(g for g in report.gates if g.gate_id == "notebook_assets")
    assert gate.status == "fail"
    assert "missing fields" in gate.failure_detail


def test_scripts_surface_gate_fails_when_script_missing(tmp_path: Path) -> None:
    root = _make_minimal_valid_root(tmp_path)
    (root / EXPECTED_SCRIPTS[0]).unlink()

    result = run_release_validation(root=root)
    report = result["report"]

    assert report.all_gates_pass is False
    gate = next(g for g in report.gates if g.gate_id == "scripts_surface")
    assert gate.status == "fail"
    assert "missing scripts" in gate.failure_detail


def test_stub_removal_gate_fails_when_stub_present(tmp_path: Path) -> None:
    root = _make_minimal_valid_root(tmp_path)
    (root / "docker" / "STUB.md").write_text("placeholder\n", encoding="utf-8")

    result = run_release_validation(root=root)
    report = result["report"]

    assert report.all_gates_pass is False
    gate = next(g for g in report.gates if g.gate_id == "stub_removal")
    assert gate.status == "fail"
    assert "docker" in gate.failure_detail


def test_test_coverage_gate_fails_when_test_file_missing(tmp_path: Path) -> None:
    root = _make_minimal_valid_root(tmp_path)
    (root / EXPECTED_PHASE6_TEST_FILES[0]).unlink()

    result = run_release_validation(root=root)
    report = result["report"]

    assert report.all_gates_pass is False
    gate = next(g for g in report.gates if g.gate_id == "test_suite_coverage")
    assert gate.status == "fail"
    assert "missing" in gate.failure_detail


def test_readme_gate_fails_when_marker_absent(tmp_path: Path) -> None:
    root = _make_minimal_valid_root(tmp_path)
    (root / "README.md").write_text("# MARBTS\n\nNo validation info.\n", encoding="utf-8")

    result = run_release_validation(root=root)
    report = result["report"]

    assert report.all_gates_pass is False
    gate = next(g for g in report.gates if g.gate_id == "readme_current")
    assert gate.status == "fail"


def test_report_file_written_when_reports_root_provided(tmp_path: Path) -> None:
    root = _make_minimal_valid_root(tmp_path)
    reports_root = tmp_path / "test_reports"

    result = run_release_validation(root=root, reports_root=reports_root)
    report_file = result["report_file"]

    assert report_file is not None
    assert Path(report_file).exists()
    payload = json.loads(Path(report_file).read_text(encoding="utf-8"))
    assert payload["schema_version"] == SCHEMA_VERSION
    assert "gates" in payload
    assert isinstance(payload["gates"], list)


# ---------------------------------------------------------------------------
# Model contract tests
# ---------------------------------------------------------------------------


def test_release_gate_rejects_invalid_status() -> None:
    from hart.models import ReleaseGate

    with pytest.raises(ValueError, match="status must be"):
        ReleaseGate(gate_id="g1", description="gate 1", status="unknown")


def test_release_gate_rejects_empty_gate_id() -> None:
    from hart.models import ReleaseGate

    with pytest.raises(ValueError, match="gate_id must be"):
        ReleaseGate(gate_id="", description="gate 1", status="pass")


def test_release_readiness_report_rejects_mismatched_counts() -> None:
    from hart.models import ReleaseGate, ReleaseReadinessReport

    gate = ReleaseGate(gate_id="g1", description="gate 1", status="pass", evidence="ok")
    with pytest.raises(ValueError, match="pass_count \\+ fail_count must equal gate_count"):
        ReleaseReadinessReport(
            schema_version=SCHEMA_VERSION,
            timestamp_utc="2026-04-24T00:00:00+00:00",
            all_gates_pass=True,
            gate_count=2,  # deliberate mismatch: 1+0 != 2
            pass_count=1,
            fail_count=0,
            gates=(gate,),
        )


def test_release_readiness_report_all_gates_pass_false_when_fail_exists(tmp_path: Path) -> None:
    root = _make_minimal_valid_root(tmp_path)
    # Remove README to guarantee at least one failing gate
    (root / "README.md").unlink()

    result = run_release_validation(root=root)
    report = result["report"]

    assert report.all_gates_pass is False
    assert report.fail_count >= 1
    assert report.pass_count + report.fail_count == report.gate_count


# ---------------------------------------------------------------------------
# Real project validation (smoke gate — verifies the actual repo passes)
# ---------------------------------------------------------------------------


def test_actual_project_passes_all_release_gates() -> None:
    """Run validation against the real project root. All gates must pass."""
    result = run_release_validation()
    report = result["report"]

    failed_gates = [g for g in report.gates if g.status == "fail"]
    if failed_gates:
        details = "\n".join(
            f"  [{g.gate_id}] {g.failure_detail}" for g in failed_gates
        )
        raise AssertionError(
            f"release validation failed on real project root:\n{details}"
        )

    assert report.all_gates_pass is True
