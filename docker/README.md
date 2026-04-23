# Docker Runtime Assets

This directory contains the concrete Phase 6 container runtime path for MARBTS.

## Contents

- `Dockerfile`: installs the packaged MARBTS CLI and default runtime inputs.
- `docker-compose.yml`: canonical profile services for baseline experiment workflows.

## Build Image

From repository root:

- `docker compose -f docker/docker-compose.yml build`

## Run Canonical Profiles

From repository root:

- Multi-seed baseline:
  - `docker compose -f docker/docker-compose.yml --profile multi-seed run --rm multi-seed-report`
- Policy matrix baseline:
  - `docker compose -f docker/docker-compose.yml --profile policy-matrix run --rm policy-experiment-matrix`
- Stress suite baseline:
  - `docker compose -f docker/docker-compose.yml --profile stress-suite run --rm stress-test-suite`
- Ablation report baseline:
  - `docker compose -f docker/docker-compose.yml --profile ablation-report run --rm ablation-report`

Outputs are written to host-mounted `artifacts/`.

## Packaged Runner (Host)

You can dispatch the same compose profiles via MARBTS CLI:

- `marbts container-profile --spec multi_seed_baseline --dry-run`
- `marbts container-profile --spec policy_matrix_baseline`
- `marbts container-profile --spec stress_suite_baseline`
- `marbts container-profile --spec ablation_report_baseline`
