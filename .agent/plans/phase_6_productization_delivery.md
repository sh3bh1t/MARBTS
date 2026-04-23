# Phase 6: Productization and Plug-and-Play Delivery

Conforms to guide files in .agent/guides/

## Objective
Convert the completed research platform into a clean-room reproducible, plug-and-play project package with production-grade developer ergonomics: installability, runnable presets, real Docker assets, notebook deliverables, and release-quality validation gates.

## Current Status

- Status: In progress
- Dependency: Requires stable outputs from Phases 1-5 (satisfied)

### Increment Progress

- Increment 1 (completed): runtime packaging and configuration presets.
- Increment 2 (next): concrete Docker runtime assets and container validation.
- Increment 3 (next): notebook deliverables and reproducible analysis workflow.
- Increment 4 (next): release-quality validation automation and readiness checklist.

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
- `ContainerExecutionSpec` (planned)
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
