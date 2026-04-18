# Docker

Optional containerized execution assets for reproducible Phase 5 research runs.

## Build

- `docker build -t marbts-phase5:latest -f docker/Dockerfile .`

## Run Phase 5 Ablation Suite

- `python scripts/run_phase5_container_command.py`

That script prints the repo-root-relative `docker run` command derived from `configs/base/phase5_container_profile.json`.

Equivalent direct invocation:

- `docker run --rm -v $PWD:/workspace -w /workspace marbts-phase5:latest /bin/sh -lc "python -m pip install -r requirements.txt && PYTHONPATH=src python scripts/run_phase5_ablation_smoke.py"`

## Notes

- Container execution is optional and intended for environment pinning, not for privileged access.
- The simulation remains fully sandboxed and synthetic inside the container as well.
