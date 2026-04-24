# MARBTS Release Readiness Checklist

This checklist defines the acceptance gates for a release-ready MARBTS project state.
Each gate is validated automatically by `scripts/run_release_validation.py` (or `marbts-release-validation`).

All 9 gates must pass before the project is considered release-ready.

---

## How to Run

```bash
# Host (PYTHONPATH required for standalone script):
PYTHONPATH=src python scripts/run_release_validation.py

# Packaged CLI (after pip install -e .):
marbts-release-validation

# With optional report file:
marbts-release-validation --reports-root artifacts/reports
```

Exits 0 if all gates pass; exits 1 if any gate fails.

---

## Gates

### 1. `packaging`
**Description:** `pyproject.toml` has all required entry points and version.

**Acceptance criteria:**
- `pyproject.toml` exists at the project root.
- `version` field is present and non-empty.
- All 7 CLI entry points are declared under `[project.scripts]`:
  - `marbts`
  - `marbts-multi-seed-report`
  - `marbts-policy-experiment-matrix`
  - `marbts-stress-test-suite`
  - `marbts-ablation-report`
  - `marbts-container-profile`
  - `marbts-release-validation`

**Failure signal:** Missing `pyproject.toml` or one or more entry points absent.

---

### 2. `config_presets`
**Description:** All experiment preset files are present and loadable.

**Acceptance criteria:**
- All 4 preset JSON files exist under `configs/experiments/`:
  - `multi_seed_baseline.json`
  - `policy_experiment_matrix_baseline.json`
  - `stress_test_suite_baseline.json`
  - `ablation_report_baseline.json`
- Each file parses without error as a valid `ExperimentPreset`.

**Failure signal:** Missing file or schema/parse error in any preset.

---

### 3. `seed_bundles`
**Description:** All seed bundle files are present and loadable.

**Acceptance criteria:**
- Both seed bundle JSON files exist under `configs/seeds/`:
  - `rule_baseline_multi_seed.json`
  - `adaptive_matrix_default.json`
- Each file parses without error as a valid `SeedBundle` (non-empty `bundle_id`, non-empty `seeds`).

**Failure signal:** Missing file or schema/parse error in any bundle.

---

### 4. `docker_assets`
**Description:** Docker runtime files are present in `docker/`.

**Acceptance criteria:**
- `docker/Dockerfile` exists.
- `docker/docker-compose.yml` exists.

**Failure signal:** Either file is absent.

---

### 5. `notebook_assets`
**Description:** All notebooks pass metadata and structural validation.

**Acceptance criteria:**
- All 3 notebook files exist under `notebooks/`:
  - `replay_and_comparative_walkthrough.ipynb`
  - `policy_matrix_walkthrough.ipynb`
  - `ablation_report_walkthrough.ipynb`
- Each notebook is valid JSON, `nbformat: 4`, has at least one code cell.
- `metadata.marbts_workflow` contains: `phase`, `workflow_id`, `generator_commands`, `required_reports`.
- At least one code cell contains the `RUN_GENERATORS` control flag and a `scripts/run_` reference.

**Failure signal:** Missing notebook, malformed JSON, unsupported nbformat, missing workflow metadata fields, or missing code cell flags.

---

### 6. `scripts_surface`
**Description:** All canonical entry-point scripts are present in `scripts/`.

**Acceptance criteria:**
- All 13 scripts exist:
  - `run_multi_seed_report.py`
  - `run_policy_experiment_matrix.py`
  - `run_stress_test_suite.py`
  - `run_ablation_report.py`
  - `run_container_profile.py`
  - `run_notebook_smoke.py`
  - `run_release_validation.py`
  - `run_comparative_report.py`
  - `run_adaptive_planning_smoke.py`
  - `run_scenario_catalog_smoke.py`
  - `run_rule_baseline_smoke.py`
  - `run_network_core_smoke.py`
  - `run_deception_hooks_smoke.py`

**Failure signal:** Any script file is absent.

---

### 7. `stub_removal`
**Description:** No `STUB.md` placeholders exist in delivery directories.

**Acceptance criteria:**
- None of these directories contain a `STUB.md` file:
  - `docker/`, `notebooks/`, `configs/`, `configs/base/`, `configs/experiments/`, `configs/seeds/`

**Failure signal:** `STUB.md` found in any of the above directories.

---

### 8. `test_suite_coverage`
**Description:** Phase 6 test files are present in `tests/`.

**Acceptance criteria:**
- All 8 Phase 6 test files exist:
  - `tests/unit/test_notebook_assets.py`
  - `tests/unit/test_container_runtime_assets.py`
  - `tests/unit/test_runtime_presets.py`
  - `tests/unit/test_marbts_cli_experiment_commands.py`
  - `tests/unit/test_release_validation.py`
  - `tests/integration/test_multi_seed_report.py`
  - `tests/integration/test_policy_experiment_matrix.py`
  - `tests/integration/test_stress_test_suite.py`

**Failure signal:** Any test file is absent.

---

### 9. `readme_current`
**Description:** `README.md` references the release validation command.

**Acceptance criteria:**
- `README.md` exists at the project root.
- The string `run_release_validation` appears somewhere in the file (confirms the release workflow is documented).

**Failure signal:** `README.md` absent or missing the release validation reference.

---

## Interpreting Results

| Output tag        | Meaning                                    |
|-------------------|--------------------------------------------|
| `RELEASE_READY`   | All 9 gates passed — project is release-ready |
| `RELEASE_NOT_READY` | One or more gates failed — see `[FAIL]` lines |
| `[PASS] gate_id`  | Gate passed; `evidence` field shows details |
| `[FAIL] gate_id`  | Gate failed; `failure_detail` field shows the specific problem |

---

## Automated Validation Contract

The programmatic equivalent of this checklist is `src/utils/release_validation.py`.
The `ReleaseReadinessReport` model (in `src/hart/models/runtime_models.py`) captures the structured output.

When the release validation script emits `RELEASE_READY` and exits 0, the project satisfies all acceptance criteria in this checklist.
