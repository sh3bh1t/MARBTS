# Phase 5 Stress Workflow

## Purpose

This document describes the initial Phase 5 research-extension workflow:

- validate a versioned scenario catalog
- run a multi-scenario stress suite
- retain complete run, metrics, and report artifacts for later paper-oriented analysis

## Primary Inputs

- Scenario catalog: `scenarios/library/catalog.json`
- Stress config: `configs/experiments/phase5_stress_matrix.json`
- Seed reference: `configs/seeds/phase5_baseline_seeds.json`

## Run Command

```bash
PYTHONPATH=src python scripts/run_phase5_stress_smoke.py
```

## Expected Outputs

- Per-run artifacts under `artifacts/runs/<run_id>/`
- Comparison reports per scenario under `artifacts/reports/phase3_unified_comparison_<scenario_id>.json`
- Stress summary under `artifacts/reports/phase5_stress_summary_<config_id>.json`

## Interpretation Notes

- The stress summary is a top-level index pointing to the underlying per-scenario comparison reports.
- Each per-scenario report preserves the Phase 3 aggregate format so Phase 4 tooling can still consume it.
- Initial Phase 5 stress execution focuses on scenario breadth and reproducible reporting rather than deception mechanics.
- Deception mechanics now exist at the run level through Blue decoy deployment and deception-trigger logging, but the stress workflow does not yet isolate decoy efficacy as a standalone experiment family.

## Related Deception Experiment

The dedicated decoy-efficacy path is run separately:

```bash
PYTHONPATH=src python scripts/run_phase5_decoy_efficacy_smoke.py
```

This produces `artifacts/reports/phase5_decoy_efficacy_<scenario_id>.json` with:
- mean final compromise under decoy-enabled versus decoy-disabled Blue policies
- mean Blue deception actions
- mean deception-trigger events
- explicit `efficacy_observed` guidance so structurally valid but behaviorally flat runs are easy to spot
