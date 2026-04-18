# Phase 5 Ablation Workflow

This workflow closes the Phase 5 research path with a standardized deception-focused ablation matrix.

## Inputs

- Scenario catalog: `scenarios/library/catalog.json`
- Ablation matrix config: `configs/experiments/phase5_ablation_matrix.json`
- Container profile: `configs/base/phase5_container_profile.json`

## Run

- Bash/Zsh: `PYTHONPATH=src python scripts/run_phase5_ablation_smoke.py`
- PowerShell: `$env:PYTHONPATH='src'; python scripts/run_phase5_ablation_smoke.py`

## Outputs

- `artifacts/reports/phase5_ablation_suite_<matrix_id>.json`
- `artifacts/reports/phase5_ablation_suite_<matrix_id>.md`
- `artifacts/reports/phase5_publication_table_<matrix_id>.json`
- `artifacts/reports/phase5_manifest_<matrix_id>.json`

## What It Measures

- final compromise under each deception/planning ablation
- Blue deception action mix split into decoy versus feint
- deception trigger counts under aggressive Red pressure

## Optional Container Reproduction

- Build image: `docker build -t marbts-phase5:latest -f docker/Dockerfile .`
- Print the canonical container command: `python scripts/run_phase5_container_command.py`

This keeps the run path repo-root relative and pinned through the checked-in Dockerfile plus container profile config.
