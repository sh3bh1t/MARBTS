# Phase 5: Advanced Research Extensions

Conforms to guide files in .agent/guides/

## Objective
Extend the platform for publication-grade experimentation via richer scenarios, decoy/bluff strategy analysis, stress testing, optional containerized execution, and comprehensive ablation studies.

## Current Status

- Status: Completed
- Dependency: Requires stable outputs from Phases 1-4

## Inputs
- Stable platform from Phases 1-4
- Baseline and adaptive policy outputs
- Initial scenario catalog and experiment harness

## Outputs
- Expanded scenario library with versioning
- Advanced strategy modules (decoy/bluff)
- Ablation and stress-test pipelines
- Optional containerized simulation profile for reproducible environments
- Paper-ready experiment package

## Components to Build
1. Scenario library manager (catalog, tags, versioning)
2. Decoy/bluff tactic primitives and policy hooks
3. Stress-test suite (scale, noise, observability constraints)
4. Ablation orchestrator and report templates
5. Optional containerization profile (sandboxed runtime)
6. Research artifact bundler (results + configs + metadata)

## Step-by-Step Implementation Tasks
1. Define scenario taxonomy (topology complexity, vulnerability density, defense posture).
2. Implement scenario registry with semantic versioning.
3. Add decoy asset and deception outcome models.
4. Integrate bluff/feint strategy options into adaptive policy pathway.
5. Create large-scale and noisy-observation stress experiments.
6. Implement standardized ablation matrix and execution automation.
7. Add optional containerized execution path with deterministic config pinning.
8. Build artifact packaging for paper appendices (tables, plots, configs, seeds).

## Data Structures Involved
- `ScenarioCatalogEntry`
- `DeceptionEvent`
- `StressTestConfig`
- `AblationMatrix`
- `ContainerExecutionConfig`
- `ResearchArtifactManifest`
- `PublicationMetricTable`

## Simulation Behavior Expected
- System supports heterogeneous scenarios without interface changes.
- Decoy/bluff mechanisms alter attacker/defender dynamics measurably.
- Stress tests expose robustness boundaries and failure profiles.
- Containerized runs reduce environment drift and improve reproducibility.

## Manual Test Cases
1. **Scenario Library Consistency Test**
   - Load multiple scenario versions and run compatibility checks.
   - Expected: deterministic loading, explicit schema/version rejection if incompatible.
2. **Decoy Effectiveness Test**
   - Enable decoy strategy in high-lateral-risk scenario.
   - Expected: measurable reduction in effective compromise progression.
3. **Stress Robustness Test**
   - Increase graph size and inject observation noise.
   - Expected: system remains stable; performance/quality degradation is quantified.
4. **Ablation Completeness Test**
   - Run full ablation matrix.
   - Expected: each ablation condition produces labeled outputs and metric bundles.
5. **Container Reproducibility Test (Optional)**
   - Execute identical experiment inside/outside container with pinned configs.
   - Expected: equivalent outputs within deterministic tolerance policy.

## Failure Modes
- Scenario drift breaks backward compatibility.
- Deception logic introduces unbounded stochastic behavior.
- Stress suite causes silent truncation or dropped events.
- Ablation reports are incomplete or mislabeled.
- Container and host runs diverge due to hidden dependency differences.

## Acceptance Criteria
- Scenario library supports controlled experiment expansion with version integrity.
- Advanced strategy features produce measurable and logged effects.
- Stress and ablation suites execute end-to-end with complete artifacts.
- Optional containerized execution path is documented and reproducible.
- Outputs are sufficient for research-paper methods/results reproducibility sections.

## Plan Revision Log
- 2026-03-28: Initial phase plan created.
- 2026-03-28: Confirmed advanced research extensions align with scenarios/experiments/docs/artifacts/docker structure.
- 2026-03-28: Updated phase path assumptions to flattened `src/*` source layout.
- 2026-03-28: Added explicit phase status tracking section.
- 2026-04-18: Began Phase 5 by adding a versioned scenario catalog, additional library scenarios, experiment/seed configs, and an initial multi-scenario stress-suite runner with summary artifacts.
- 2026-04-18: Added initial decoy/deception support through a Blue-team `decoy` action, decoy-triggered exploit outcomes, deception-aware logging, and baseline metric coverage.
- 2026-04-18: Added a dedicated decoy-efficacy experiment runner/report that isolates decoy-enabled versus decoy-disabled Blue behavior over seeded runs and records deception-focused efficacy deltas.
- 2026-04-18: Added a dedicated aggressive Red experiment policy and decoy-biased Blue planning mode for the decoy-efficacy path so deception scenarios produce measurable activity without altering the Phase 2 baseline.
- 2026-04-18: Completed Phase 5 by adding bluff/feint deception mechanics, a standardized deception ablation matrix with publication-ready bundle outputs, and an optional containerized reproduction path driven by checked-in config.
