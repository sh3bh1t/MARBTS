from __future__ import annotations

import dataclasses
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

from hart.models import ReleaseGate, ReleaseReadinessReport
from utils.runtime_presets import load_experiment_preset, load_seed_bundle

SCHEMA_VERSION = "2026-04-24.release_readiness.v1"

EXPECTED_ENTRY_POINTS: tuple[str, ...] = (
    "marbts = ",
    "marbts-multi-seed-report = ",
    "marbts-policy-experiment-matrix = ",
    "marbts-stress-test-suite = ",
    "marbts-ablation-report = ",
    "marbts-container-profile = ",
    "marbts-release-validation = ",
)

EXPECTED_PRESET_FILES: tuple[str, ...] = (
    "configs/experiments/multi_seed_baseline.json",
    "configs/experiments/policy_experiment_matrix_baseline.json",
    "configs/experiments/stress_test_suite_baseline.json",
    "configs/experiments/ablation_report_baseline.json",
)

EXPECTED_SEED_BUNDLE_FILES: tuple[str, ...] = (
    "configs/seeds/rule_baseline_multi_seed.json",
    "configs/seeds/adaptive_matrix_default.json",
)

EXPECTED_DOCKER_FILES: tuple[str, ...] = (
    "docker/Dockerfile",
    "docker/docker-compose.yml",
)

EXPECTED_NOTEBOOK_FILES: tuple[str, ...] = (
    "notebooks/replay_and_comparative_walkthrough.ipynb",
    "notebooks/policy_matrix_walkthrough.ipynb",
    "notebooks/ablation_report_walkthrough.ipynb",
)

_NOTEBOOK_REQUIRED_WORKFLOW_FIELDS: tuple[str, ...] = (
    "phase",
    "workflow_id",
    "generator_commands",
    "required_reports",
)

EXPECTED_SCRIPTS: tuple[str, ...] = (
    "scripts/run_multi_seed_report.py",
    "scripts/run_policy_experiment_matrix.py",
    "scripts/run_stress_test_suite.py",
    "scripts/run_ablation_report.py",
    "scripts/run_container_profile.py",
    "scripts/run_notebook_smoke.py",
    "scripts/run_release_validation.py",
    "scripts/run_comparative_report.py",
    "scripts/run_adaptive_planning_smoke.py",
    "scripts/run_scenario_catalog_smoke.py",
    "scripts/run_rule_baseline_smoke.py",
    "scripts/run_network_core_smoke.py",
    "scripts/run_deception_hooks_smoke.py",
)

STUB_CHECK_DIRS: tuple[str, ...] = (
    "docker",
    "notebooks",
    "configs",
    "configs/base",
    "configs/experiments",
    "configs/seeds",
)

EXPECTED_PHASE6_TEST_FILES: tuple[str, ...] = (
    "tests/unit/test_notebook_assets.py",
    "tests/unit/test_container_runtime_assets.py",
    "tests/unit/test_runtime_presets.py",
    "tests/unit/test_marbts_cli_experiment_commands.py",
    "tests/unit/test_release_validation.py",
    "tests/integration/test_multi_seed_report.py",
    "tests/integration/test_policy_experiment_matrix.py",
    "tests/integration/test_stress_test_suite.py",
)

README_RELEASE_MARKER = "run_release_validation"

_GateCheckResult = tuple[bool, str, str]  # (passed, evidence, failure_detail)


def _check_packaging(root: Path) -> _GateCheckResult:
    pyproject = root / "pyproject.toml"
    if not pyproject.exists():
        return False, "", "pyproject.toml not found"
    text = pyproject.read_text(encoding="utf-8")
    missing = [ep for ep in EXPECTED_ENTRY_POINTS if ep not in text]
    if missing:
        found = len(EXPECTED_ENTRY_POINTS) - len(missing)
        return (
            False,
            f"found {found}/{len(EXPECTED_ENTRY_POINTS)} entry points",
            f"missing entry points: {missing}",
        )
    version = ""
    for line in text.splitlines():
        stripped = line.strip()
        if stripped.startswith("version") and "=" in stripped:
            version = stripped.split("=", 1)[1].strip().strip('"')
            break
    return True, f"version={version!r}, entry_points={len(EXPECTED_ENTRY_POINTS)}", ""


def _check_config_presets(root: Path) -> _GateCheckResult:
    missing = [f for f in EXPECTED_PRESET_FILES if not (root / f).exists()]
    if missing:
        return False, "", f"missing preset files: {missing}"
    load_errors: list[str] = []
    loaded_ids: list[str] = []
    for preset_file in EXPECTED_PRESET_FILES:
        try:
            preset = load_experiment_preset(root / preset_file)
            loaded_ids.append(preset.preset_id)
        except Exception as exc:
            load_errors.append(f"{preset_file}: {exc}")
    if load_errors:
        return False, f"partially loaded: {loaded_ids}", f"load errors: {load_errors}"
    return True, f"preset_ids={','.join(loaded_ids)}", ""


def _check_seed_bundles(root: Path) -> _GateCheckResult:
    missing = [f for f in EXPECTED_SEED_BUNDLE_FILES if not (root / f).exists()]
    if missing:
        return False, "", f"missing seed bundle files: {missing}"
    load_errors: list[str] = []
    loaded_ids: list[str] = []
    for bundle_file in EXPECTED_SEED_BUNDLE_FILES:
        try:
            bundle = load_seed_bundle(root / bundle_file)
            loaded_ids.append(bundle.bundle_id)
        except Exception as exc:
            load_errors.append(f"{bundle_file}: {exc}")
    if load_errors:
        return False, f"partially loaded: {loaded_ids}", f"load errors: {load_errors}"
    return True, f"bundle_ids={','.join(loaded_ids)}", ""


def _check_docker_assets(root: Path) -> _GateCheckResult:
    missing = [f for f in EXPECTED_DOCKER_FILES if not (root / f).exists()]
    if missing:
        return False, "", f"missing docker files: {missing}"
    return True, f"docker_files={len(EXPECTED_DOCKER_FILES)}", ""


def _check_notebook_assets(root: Path) -> _GateCheckResult:
    validated_ids: list[str] = []
    for nb_path_str in EXPECTED_NOTEBOOK_FILES:
        nb_path = root / nb_path_str
        if not nb_path.exists():
            return False, "", f"notebook not found: {nb_path_str}"
        try:
            payload = json.loads(nb_path.read_text(encoding="utf-8"))
        except Exception as exc:
            return False, "", f"notebook JSON parse error ({nb_path_str}): {exc}"
        if payload.get("nbformat") != 4:
            return False, "", f"unsupported nbformat in: {nb_path_str}"
        metadata = payload.get("metadata") or {}
        workflow = metadata.get("marbts_workflow") or {}
        missing_fields = [f for f in _NOTEBOOK_REQUIRED_WORKFLOW_FIELDS if f not in workflow]
        if missing_fields:
            return False, "", f"notebook workflow missing fields {missing_fields}: {nb_path_str}"
        code_cells = [c for c in payload.get("cells", []) if c.get("cell_type") == "code"]
        if not code_cells:
            return False, "", f"notebook has no code cells: {nb_path_str}"
        source_blob = "\n".join(
            "".join(c.get("source", []))
            for c in code_cells
            if isinstance(c.get("source"), list)
        )
        if "RUN_GENERATORS" not in source_blob:
            return False, "", f"notebook missing RUN_GENERATORS flag: {nb_path_str}"
        validated_ids.append(str(workflow.get("workflow_id", "unknown")))
    return True, f"notebook_count={len(validated_ids)}, workflows={','.join(validated_ids)}", ""


def _check_scripts_surface(root: Path) -> _GateCheckResult:
    missing = [s for s in EXPECTED_SCRIPTS if not (root / s).exists()]
    if missing:
        found = len(EXPECTED_SCRIPTS) - len(missing)
        return False, f"found {found}/{len(EXPECTED_SCRIPTS)} scripts", f"missing scripts: {missing}"
    return True, f"script_count={len(EXPECTED_SCRIPTS)}", ""


def _check_stub_removal(root: Path) -> _GateCheckResult:
    stubs_found = [d for d in STUB_CHECK_DIRS if (root / d / "STUB.md").exists()]
    if stubs_found:
        return False, "", f"STUB.md found in: {stubs_found}"
    return True, f"checked_dirs={len(STUB_CHECK_DIRS)}", ""


def _check_test_coverage(root: Path) -> _GateCheckResult:
    missing = [f for f in EXPECTED_PHASE6_TEST_FILES if not (root / f).exists()]
    if missing:
        found = len(EXPECTED_PHASE6_TEST_FILES) - len(missing)
        return False, f"found {found}/{len(EXPECTED_PHASE6_TEST_FILES)} test files", f"missing: {missing}"
    return True, f"test_file_count={len(EXPECTED_PHASE6_TEST_FILES)}", ""


def _check_readme_current(root: Path) -> _GateCheckResult:
    readme = root / "README.md"
    if not readme.exists():
        return False, "", "README.md not found"
    text = readme.read_text(encoding="utf-8")
    if README_RELEASE_MARKER not in text:
        return False, "", f"README.md missing release validation reference ('{README_RELEASE_MARKER}')"
    return True, f"marker={README_RELEASE_MARKER!r}", ""


_GATE_DEFINITIONS: tuple[tuple[str, str, Callable[[Path], _GateCheckResult]], ...] = (
    ("packaging", "pyproject.toml has all required entry points and version", _check_packaging),
    ("config_presets", "all experiment preset files present and loadable", _check_config_presets),
    ("seed_bundles", "all seed bundle files present and loadable", _check_seed_bundles),
    ("docker_assets", "Docker runtime files present in docker/", _check_docker_assets),
    ("notebook_assets", "all notebooks pass metadata and structure validation", _check_notebook_assets),
    ("scripts_surface", "all canonical entry-point scripts present in scripts/", _check_scripts_surface),
    ("stub_removal", "no STUB.md placeholders in delivery directories", _check_stub_removal),
    ("test_suite_coverage", "Phase 6 test files present in tests/", _check_test_coverage),
    ("readme_current", "README.md references release validation command", _check_readme_current),
)


def _detect_project_root() -> Path:
    candidate = Path(__file__).resolve().parent
    for parent in [candidate, *candidate.parents]:
        if (parent / "pyproject.toml").exists():
            return parent
    return Path.cwd()


def run_release_validation(
    root: Path | None = None,
    reports_root: Path | None = None,
) -> dict[str, Any]:
    resolved_root = root if root is not None else _detect_project_root()
    timestamp_utc = datetime.now(timezone.utc).isoformat()

    gates: list[ReleaseGate] = []
    for gate_id, description, check_fn in _GATE_DEFINITIONS:
        passed, evidence, failure_detail = check_fn(resolved_root)
        gates.append(
            ReleaseGate(
                gate_id=gate_id,
                description=description,
                status="pass" if passed else "fail",
                evidence=evidence,
                failure_detail=failure_detail,
            )
        )

    pass_count = sum(1 for g in gates if g.status == "pass")
    fail_count = len(gates) - pass_count

    report = ReleaseReadinessReport(
        schema_version=SCHEMA_VERSION,
        timestamp_utc=timestamp_utc,
        all_gates_pass=(fail_count == 0),
        gate_count=len(gates),
        pass_count=pass_count,
        fail_count=fail_count,
        gates=tuple(gates),
    )

    report_file: str | None = None
    if reports_root is not None:
        reports_root.mkdir(parents=True, exist_ok=True)
        report_file = str(reports_root / "release_readiness_report.json")
        Path(report_file).write_text(
            json.dumps(dataclasses.asdict(report), indent=2),
            encoding="utf-8",
        )

    return {"report": report, "report_file": report_file}
