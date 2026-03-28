# Phase 2: Rule-Based Agents

Conforms to guide files in copilot/guides/

## Objective
Implement deterministic, explainable Red and Blue rule-based policies integrated into the turn-based orchestrator for baseline benchmarking.

## Inputs
- Phase 1 environment engine and legal action generator
- Agent interface contract from master plan
- Deterministic seed controls and logging schema

## Outputs
- Rule-based Red policy module
- Rule-based Blue policy module
- Policy evaluation hooks in orchestrator
- Action rationale payloads attached to every decision

## Components to Build
1. Policy interface (`select_action(state, legal_actions, context) -> ActionIntent`)
2. Red heuristic policy (scan -> exploit -> lateral -> escalation priorities)
3. Blue heuristic policy (monitor -> patch -> block -> isolate priorities)
4. Decision explainability formatter
5. Policy-level telemetry counters

## Step-by-Step Implementation Tasks
1. Define policy plugin interface and registration mechanism.
2. Implement Red scoring heuristics (expected gain, path expansion, escalation potential).
3. Implement Blue scoring heuristics (threat suppression, containment urgency, resilience impact).
4. Add deterministic tie-breakers for equal-scored actions.
5. Emit decision rationale and confidence/utility estimates in action intents.
6. Integrate both policies into orchestrator action cycle.
7. Add baseline scenarios to validate predictable behavior.
8. Record per-policy performance counters in metrics stream.

## Data Structures Involved
- `PolicyContext`
- `ActionCandidate`
- `DecisionRationale`
- `PolicyScoreBreakdown`
- `ActionIntent`
- `ActionOutcome`
- `PolicyMetricsSnapshot`

## Simulation Behavior Expected
- Red policy consistently follows staged offensive progression when legal.
- Blue policy prioritizes containment and risk reduction under observed threats.
- Decisions are deterministic under fixed seed and tie-break rules.
- Every action includes machine-readable rationale payload.

## Manual Test Cases
1. **Red Progression Test**
   - Scenario with reachable vulnerable path.
   - Expected: red executes scan/exploit/lateral/escalation sequence when preconditions are met.
2. **Blue Containment Test**
   - Introduce compromised node and high lateral risk.
   - Expected: blue selects isolate/block before low-impact patching.
3. **Tie-Break Determinism Test**
   - Two actions with equal utility.
   - Expected: consistent deterministic action selection across reruns.
4. **Explainability Payload Test**
   - Inspect action logs for 10 timesteps.
   - Expected: every action has rationale, score summary, predicted effect.
5. **Rule Regression Test**
   - Replay fixed scenario with same seed.
   - Expected: same action sequence hash and final compromise counts.

## Failure Modes
- Heuristic instability causing non-deterministic action ranking.
- Action chosen outside legal action set.
- Rationale missing or not aligned with actual scoring path.
- Blue policy deadlocks by repeatedly selecting ineffective monitor-only actions.
- Red policy skips prerequisite phases without valid conditions.

## Acceptance Criteria
- Rule-based policies produce deterministic trajectories under fixed seeds.
- All selected actions are legal and schema-valid.
- Explainability fields are complete for 100% of decisions.
- Baseline metrics are generated for later adaptive comparisons.
- Manual tests pass without silent policy exceptions.

## Plan Revision Log
- 2026-03-28: Initial phase plan created.
