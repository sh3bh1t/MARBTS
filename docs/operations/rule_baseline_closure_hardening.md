# Rule Baseline Closure Hardening

Conforms to guide files in .agent/guides/

## Scope
This document defines closure hardening checks for the rule baseline implementation.

## Hardening Checks

1. **Policy Contract Integrity**
   - Shared policy contracts are centralized in `src/hart/models/policy_models.py`.
   - Policy interface and registry are implemented in `src/agents/interfaces/policy.py`.

2. **Deterministic Rule Policies**
   - Red and Blue rule-based policies select legal actions using deterministic ranking and tie-breakers.
   - Explainability payload includes summary, predicted effect, confidence, utility estimate, and score breakdown.

3. **Kernel Integration Correctness**
   - Policy decisions are integrated into the timestep loop when no custom selector override is provided.
   - Legacy selector path remains compatible for deterministic test control.

4. **Policy Telemetry & Metrics**
   - Per-run policy telemetry is persisted in `artifacts/runs/<run_id>/policy_metrics.json`.
   - Baseline metrics are persisted in `artifacts/metrics/<run_id>.json`.
   - Multi-seed aggregate report is persisted in `artifacts/reports/multi_seed_report_<scenario_id>.json`.

5. **Reproducibility & Regression**
   - Same-seed sequence-hash reproducibility test is in `tests/reproducibility/test_rule_baseline_reproducibility.py`.
   - Baseline sequence-hash regression lock is in `tests/regression/test_rule_baseline_regression.py`.

6. **Report Stability Bands**
   - Multi-seed aggregate includes mean/stddev/min/max where applicable.
   - Deterministic consistency indicator (`deterministic_consistency_ratio`) is included and validated.

## Recommended Closure Commands

- `python -m pytest -q`
- PowerShell: `$env:PYTHONPATH='src'; python scripts/run_rule_baseline_smoke.py`
- PowerShell: `$env:PYTHONPATH='src'; python scripts/run_multi_seed_report.py --seeds 20260329,20260330,20260331 --horizon 8`

## Expected Evidence

- Pytest suite passes with rule baseline unit/integration/simulation/reproducibility/regression checks.
- Smoke script outputs `RULE_BASELINE_SMOKE_OK`.
- Multi-seed script outputs `MULTI_SEED_REPORT_OK`.
- Generated artifacts:
  - `artifacts/runs/<run_id>/policy_metrics.json`
  - `artifacts/metrics/<run_id>.json`
   - `artifacts/reports/multi_seed_report_<scenario_id>.json`

## Status

- Phase 2 closure hardening completed.