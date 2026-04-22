# Phase 3: Adaptive Autonomy (LLM/RL)

Conforms to guide files in .agent/guides/

## Objective
Introduce adaptive agent policies (LLM reasoning and/or RL) through the same policy interface while preserving safety, explainability, and reproducibility controls.

## Current Status

- Status: In progress
- Prerequisite: Phase 2 baseline policies required (satisfied)

### Increment Progress

- Increment 1 (completed):
   - Implemented deterministic adaptive planning policy adapter at `src/agents/adaptive/planning.py`
   - Added adaptive shared contracts in `src/hart/models/policy_models.py`:
      - `AdaptivePolicyConfig`
      - `PlanningTrace`
      - `ValueEstimate`
      - `ModelInferenceRecord`
   - Added adaptive policy unit coverage (`tests/unit/test_agents_adaptive.py`)
   - Added Phase 3 smoke execution script (`scripts/run_phase3_smoke.py`)
   - Removed replaced scaffold stub (`src/agents/adaptive/STUB.md`)

- Increment 2 (next):
   - Add adaptive-vs-rule experiment matrix runner with multi-seed aggregate comparison outputs
   - Add ablation toggles (`no_planning`, `reduced_observability`) and labeled report metadata

## Inputs
- Stable rule-based baseline from Phase 2
- Shared policy interface and logging contracts
- Scenario library and seeded experiment harness

## Outputs
- At least one adaptive policy implementation (LLM or RL)
- Multi-step planning capability
- Controlled comparison harness vs rule-based baselines
- Additional metadata for adaptive decision diagnostics

## Components to Build
1. Adaptive policy adapter (compatible with existing policy interface)
2. LLM reasoning pipeline OR RL policy inference/training loop
3. Multi-step planner with bounded horizon
4. Optional decoy/bluff strategy module
5. Safety filters for action proposals
6. Adaptive-policy reproducibility controls (seed + config pinning)

## Step-by-Step Implementation Tasks
1. Select adaptive path(s): LLM-only, RL-only, or dual-track.
2. Implement adapter translating model output to legal `ActionIntent` objects.
3. Add safety guardrails to reject non-legal/non-sandbox actions.
4. Implement bounded multi-step planning objective (k-step horizon).
5. Add utility/value tracing for adaptive choices.
6. Integrate optional decoy/bluff strategy logic behind feature flags.
7. Build experiment matrix comparing adaptive vs rule-based pairings.
8. Add ablation toggles (no-planning, no-decoy, reduced-observability).

## Data Structures Involved
- `AdaptivePolicyConfig`
- `PlanningTrace`
- `ValueEstimate`
- `ModelInferenceRecord`
- `AblationConfig`
- `ExperimentCondition`
- `ComparisonMetricBundle`

## Simulation Behavior Expected
- Adaptive agents select legal actions informed by broader context than fixed heuristics.
- Multi-step planning can produce anticipatory actions (e.g., preemptive isolation/decoy).
- Decision traces are captured for post-hoc explainability.
- Comparative runs produce statistically analyzable outcomes.

## Manual Test Cases
1. **Legal Action Compliance Test**
   - Force adaptive policy under adversarial prompt/state ambiguity.
   - Expected: adapter emits only legal, schema-valid actions.
2. **Multi-Step Planning Test**
   - Scenario where short-term sacrifice yields long-term gain.
   - Expected: planner selects action with improved k-step utility.
3. **Adaptive vs Baseline Comparison Smoke Test**
   - Run small experiment matrix with fixed seeds.
   - Expected: reproducible summary tables generated.
4. **Ablation Toggle Test**
   - Disable planning/decoy modules.
   - Expected: measurable behavior shift and correctly labeled experiment outputs.
5. **Reproducibility Control Test**
   - Repeat same adaptive config + seed + scenario.
   - Expected: output variance bounded and documented per deterministic tolerance policy.

## Failure Modes
- Model outputs actions outside legal space.
- Undocumented nondeterminism from model/runtime settings.
- Explainability traces missing or too coarse for diagnosis.
- Planner horizon explosion causing unacceptable timestep latency.
- Ablation flags not properly isolating component effects.

## Acceptance Criteria
- Adaptive policy integrates without breaking policy interface contract.
- All adaptive actions pass legality and schema checks.
- Comparison experiments are reproducible under documented settings.
- Ablation studies execute and produce differentiable metric outcomes.
- Manual tests pass and failure tolerance is explicitly documented.

## Plan Revision Log
- 2026-03-28: Initial phase plan created.
- 2026-03-28: Confirmed adaptive policy components align with `src/agents/adaptive` and experiments layout.
- 2026-03-28: Updated phase path assumptions to flattened `src/*` source layout.
- 2026-03-28: Added explicit phase status tracking section.
- 2026-04-23: Started Phase 3 with Increment 1 adaptive planning scaffold, safety legality filtering, and shared adaptive rationale contracts.
- 2026-04-23: Added Phase 3 smoke runner and adaptive policy unit tests; validated deterministic adaptive traces under fixed seed.
