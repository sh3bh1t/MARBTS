# Phase 4: Logging and Visualization

Conforms to guide files in .agent/guides/

## Objective
Implement production-quality observability: complete structured logging, run provenance, trajectory replay, and research-oriented visual analytics.

## Current Status

- Status: In progress
- Dependency: Builds on simulation outputs from Phases 1-3

### Increment Progress

- Increment 1 (in progress): shared observability contracts, schema validation, provenance capture, and structured run artifact envelopes.
- Increment 2 (next): replay utilities and comparative report packaging.

## Inputs
- Event contracts and required log fields from master plan + guides
- Simulation outputs from Phases 1-3
- Metric definitions and experiment identifiers

## Outputs
- Structured event log pipeline
- Schema-validated run artifacts
- Visualization dashboards/reports for trajectory and metrics
- Replayable simulation traces

## Components to Build
1. Event schema validator and serializer
2. Observability backend abstraction (file/DB)
3. State diff and action rationale recorder
4. Run metadata/provenance recorder
5. Replay engine from event stream
6. Visualization/report generator (time-series + comparative plots)

## Step-by-Step Implementation Tasks
1. Finalize event schema versions for action/state/metric events.
2. Implement append-only event writer with integrity checks.
3. Add required provenance metadata (seed, config hash, commit hash, scenario id).
4. Implement post-run artifact packaging (logs + summaries + metadata).
5. Build replay utility to reconstruct state trajectory from logs.
6. Implement plots/tables for compromise trend, defense efficiency, response latency.
7. Add completeness checks that fail runs with missing mandatory fields.
8. Add compatibility layer for comparative experiment reports.

## Data Structures Involved
- `EventEnvelope`
- `StateDiffRecord`
- `ActionDecisionRecord`
- `MetricDeltaRecord`
- `RunProvenance`
- `ReplayFrame`
- `ExperimentSummary`

## Simulation Behavior Expected
- Every timestep emits complete, schema-valid records.
- Runs are auditable and reproducible using provenance metadata.
- Replay reconstructs trajectory without ambiguity.
- Visual outputs support direct interpretation for paper figures/tables.

## Manual Test Cases
1. **Schema Compliance Test**
   - Validate full run log against event schema.
   - Expected: zero missing required fields.
2. **Replay Fidelity Test**
   - Reconstruct trajectory from logs and compare with original snapshots.
   - Expected: equivalent final state and per-step key deltas.
3. **Provenance Integrity Test**
   - Inspect run metadata package.
   - Expected: seed/scenario/config hash/commit hash present and consistent.
4. **Comparative Visualization Test**
   - Load two baseline runs and generate comparison report.
   - Expected: charts/tables include required metrics and labels.
5. **Logging Failure Injection Test**
   - Remove required field in synthetic event.
   - Expected: validator rejects event and marks run invalid.

## Failure Modes
- Partial logs accepted without hard failure.
- Replay cannot reproduce transitions due to missing diffs.
- Provenance metadata inconsistent across artifacts.
- Visualization layer silently drops invalid data points.
- Event volume creates unacceptable write latency.

## Acceptance Criteria
- Log completeness ratio is 100% for required schema fields.
- Replay fidelity checks pass on canonical scenarios.
- Provenance metadata is complete and internally consistent.
- Visualization outputs generated for all mandatory metrics.
- Manual tests pass with explicit artifact evidence.

## Plan Revision Log
- 2026-03-28: Initial phase plan created.
- 2026-03-28: Confirmed observability modules align with `src/observability`, `src/metrics`, and `src/visualization`.
- 2026-03-28: Updated phase path assumptions to flattened `src/*` source layout.
- 2026-03-28: Added explicit phase status tracking section.
- 2026-04-23: Began phase 4 with shared observability contracts under `src/observability`, schema validation, provenance capture, and structured run artifact envelopes.
