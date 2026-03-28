# Metrics Artifacts

This directory stores per-run computed baseline metrics artifacts.

Current writer:
- `scripts/run_phase2_smoke.py` writes `artifacts/metrics/<run_id>.json`

Baseline metrics artifact includes:
- run/scenario metadata
- deterministic action sequence hash
- security outcome counters
- policy performance counters

Do not treat generated metrics as source-of-truth configuration.