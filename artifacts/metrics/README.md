# Metrics Artifacts

This directory stores per-run computed baseline metrics artifacts.

Current writers:
- `scripts/run_rule_baseline_smoke.py` writes `artifacts/metrics/<run_id>.json`
- `scripts/run_multi_seed_report.py` writes per-run baseline metric artifacts during seed sweeps
- `scripts/run_policy_experiment_matrix.py` writes per-run baseline metric artifacts during condition matrices
- `scripts/run_stress_test_suite.py` writes per-run baseline metric artifacts during stress-profile batches

Baseline metrics artifact includes:
- run/scenario metadata
- deterministic action sequence hash
- security outcome counters
- policy performance counters

Do not treat generated metrics as source-of-truth configuration.