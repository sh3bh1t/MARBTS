# Phase 6: Productization and Plug-and-Play Delivery

Conforms to guide files in .agent/guides/

## Objective
Convert the completed research platform into a clean-room reproducible, plug-and-play project package with production-grade developer ergonomics: installability, runnable presets, real Docker assets, notebook deliverables, and release-quality validation gates.

## Current Status

- Status: In progress
- Dependency: Requires stable outputs from Phases 1-5 (satisfied)

### Increment Progress

- Increment 1 (completed): runtime packaging and configuration presets.
- Increment 2 (completed): concrete Docker runtime assets and container validation.
- Increment 3 (completed): notebook deliverables and reproducible analysis workflow.
- Increment 4 (completed): release-quality validation automation and readiness checklist.

## Inputs
- Phase 1-5 runtime modules, scripts, and tests
- Scenario catalog and experiment matrix outputs
- Current reproducibility and observability artifacts

## Outputs
- Plug-and-play local bootstrap path (no ad-hoc environment steps)
- Real container assets in `docker/` (replacing scaffold stub)
- Versioned config presets in `configs/` (replacing scaffold stubs)
- Curated notebook set in `notebooks/` (replacing scaffold stub)
- Release-readiness checklist and pass/fail gate report

## Components to Build
1. Packaging/bootstrap entry path (`pyproject.toml` and/or installable CLI surface)
2. Runtime configuration presets and seed bundles (`configs/base`, `configs/experiments`, `configs/seeds`)
3. Docker execution assets (Dockerfile + compose/profile runner)
4. Notebook analysis pack (replay, matrix, and ablation walkthrough notebooks)
5. Validation automation bundle (clean-room install, container parity, notebook smoke)
6. Delivery checklist and release docs

## Step-by-Step Implementation Tasks
1. Define install mode and command surface for plug-and-play usage.
2. Add canonical config files consumed by scripts (instead of implicit defaults only).
3. Implement Docker assets that can execute baseline/matrix/ablation workflows.
4. Add notebook templates for key experiment interpretation paths.
5. Add CI-style local validation script covering full suite + key smoke runners.
6. Add release checklist document with explicit acceptance gates.
7. Remove scaffold stubs from `docker/`, `notebooks/`, and `configs/*` as real assets land.

## Data Structures Involved
- `RuntimeConfig` (implemented in `src/hart/models/runtime_models.py`)
- `ExperimentPreset` (implemented in `src/hart/models/runtime_models.py`)
- `SeedBundle` (implemented in `src/hart/models/runtime_models.py`)
- `ContainerExecutionSpec` (implemented in `src/hart/models/runtime_models.py`)
- `NotebookRunSummary` (planned)
- `ReleaseReadinessReport` (planned)

## Simulation Behavior Expected
- Contributors can set up and run baseline workflows from a clean checkout with minimal commands.
- Containerized execution path is operational (not metadata-only).
- Notebook workflows reproduce and explain outputs without bespoke local hacks.
- Release gate validation prevents drift between docs, scripts, and runnable behavior.

## Manual Test Cases
1. **Clean-Room Bootstrap Test**
   - Fresh environment, follow README install/run commands only.
   - Expected: baseline and matrix commands succeed without manual path surgery.
2. **Docker Runtime Test**
   - Build and run containerized baseline + matrix flow.
   - Expected: artifacts generated and schema-valid.
3. **Notebook Smoke Test**
   - Execute notebook cells end-to-end with pinned dependencies.
   - Expected: no missing imports, outputs generated as documented.
4. **Config Preset Integrity Test**
   - Run scripts via preset configs and explicit seed bundles.
   - Expected: deterministic outputs match baseline tolerance.
5. **Release Gate Test**
   - Execute full validation bundle.
   - Expected: checklist marks all required gates as pass.

## Failure Modes
- Plug-and-play path still depends on hidden local environment assumptions.
- Docker assets diverge from host execution behavior.
- Notebook examples drift from script APIs and fail in fresh environments.
- Config presets become stale and are not consumed by scripts.
- Release checks are incomplete and allow broken documentation/commands.

## Acceptance Criteria
- `docker/`, `notebooks/`, and `configs/*` scaffolds are replaced by real runnable assets.
- A clean checkout can run canonical workflows using documented commands only.
- Containerized execution is validated and reproducible against host tolerance policy.
- Notebook pack is executable and aligned with current APIs.
- Release-readiness checklist passes with explicit artifact evidence.

## Plan Revision Log
- 2026-04-24: Initial phase plan created after full `.agent` and `idea-core` audit identified remaining productization gaps despite Phase 5 research completion.
- 2026-04-24: Completed Increment 1 by adding installable packaging (`pyproject.toml`), packaged CLI entry points (`src/marbts_cli`), canonical preset loader/contracts (`src/utils/runtime_presets.py`, `src/hart/models/runtime_models.py`), and real preset/seed bundles under `configs/` with script integration via `--config`.
- 2026-04-24: Completed Increment 2 by replacing `docker/` stub with runnable Dockerfile/compose profiles, adding canonical `ContainerExecutionSpec` contracts/utilities, and validating container profile command wiring via unit coverage.
- 2026-04-24: Completed Increment 3 by replacing `notebooks/` stub with reproducible walkthrough notebooks (`replay_and_comparative_walkthrough.ipynb`, `policy_matrix_walkthrough.ipynb`, `ablation_report_walkthrough.ipynb`), adding notebook usage documentation (`notebooks/README.md`), and introducing notebook smoke validation coverage (`scripts/run_notebook_smoke.py`, `tests/unit/test_notebook_assets.py`).
- 2026-04-24: Completed Increment 4 by adding `ReleaseGate` and `ReleaseReadinessReport` models (`src/hart/models/runtime_models.py`), core 9-gate validation logic (`src/utils/release_validation.py`), release validation script entry point (`scripts/run_release_validation.py`), packaged CLI command (`src/marbts_cli/release_commands.py`, `marbts-release-validation` entry point in `pyproject.toml`), full unit test coverage (`tests/unit/test_release_validation.py` including real-project smoke gate), and human-readable release acceptance checklist (`docs/release_readiness_checklist.md`).
- 2026-04-24: Post-Phase-6 simulation depth overhaul. Added `watch_sim.py` as the canonical live viewer (animated, turn-by-turn, 1.5 s/turn by default). Key implementation work: probabilistic exploit resistance (`max(0.25, 1 - (sec-1)/10)`) wired into `apply_exploit` + `run_turn_based_simulation`; `decision_noise` and `node_security_level` added to the adaptive planning system enabling genuine seed-dependent variability; `enterprise_medium.json` redesigned as v2.0.0 with numeric-prefix node naming ensuring correct alphabetical ordering by security tier; `SimulationRunResult.graph_snapshots` stores per-turn graph state for correct network topology display within turns; `watch_sim.py` uses asymmetric configs (Red: `exploration_bias=4.0, decision_noise=4.0`; Blue: `exploration_bias=2.5, decision_noise=3.5, reduced_observability=True`) to create strategic asymmetry (Red spreads through perimeter; Blue fortifies crown jewels) with a 4/20–13/20 outcome range across seeds mapped to five verdict tiers (BLUE HOLDS / BLUE ADVANTAGE / CONTESTED / RED ADVANTAGE / RED WINS). All 85 tests pass.
