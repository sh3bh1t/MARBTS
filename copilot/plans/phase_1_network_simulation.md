# Phase 1: Network Simulation Core

Conforms to guide files in copilot/guides/

## Objective
Build a deterministic, graph-based simulation environment using `networkx` with strict state transition rules and complete per-timestep observability scaffolding.

## Inputs
- Master architecture and data-contract requirements from `copilot/plans/master_plan.md`
- Scenario definitions (initial JSON/YAML schema for node/edge topology)
- Fixed seed policy for deterministic execution

## Outputs
- Environment engine module (graph state initialization + transition API)
- Schema definitions for scenario, node state, and timestep snapshot
- Deterministic turn kernel stub
- Baseline logging scaffolding for state diffs

## Components to Build
1. Scenario schema + validator
2. Graph initializer (`networkx`)
3. State repository and immutable snapshot references
4. Transition engine for abstract Red/Blue action effects
5. Legal action generator per role and state
6. Seed manager and RNG wrapper
7. Timestep logger scaffold

## Step-by-Step Implementation Tasks
1. Define strict schemas for node/edge/scenario metadata and validate inputs.
2. Implement graph builder from validated scenarios.
3. Add node attributes: services, vulnerabilities, security_level, compromised_state.
4. Implement transition primitives (compromise level up/down, isolate, patch impact, block impact).
5. Implement legal action resolver enforcing sandboxed abstract actions only.
6. Build deterministic RNG wrapper and ensure all stochastic transitions use it.
7. Add timestep pre-state/post-state diff generation.
8. Produce minimal simulation kernel loop (without advanced policy logic).

## Data Structures Involved
- `ScenarioConfig`
- `NodeState`
- `EdgeState`
- `SimulationState`
- `ActionIntent`
- `ActionOutcome`
- `TimestepLogEntry`
- `RunMetadata`

## Simulation Behavior Expected
- Environment loads a scenario graph and initializes node attributes.
- At each timestep, legal action space can be computed for Red and Blue.
- Transition effects update the graph state predictably under fixed seeds.
- State snapshots and diffs are captured without missing required fields.

## Manual Test Cases
1. **Schema Rejection Test**
   - Input scenario missing required node attribute.
   - Expected: validation fails with explicit error; no simulation starts.
2. **Seed Reproducibility Test**
   - Run same scenario twice with identical seed and fixed action sequence.
   - Expected: identical post-state hashes and metric deltas.
3. **Transition Correctness Test**
   - Apply synthetic exploit action to eligible node.
   - Expected: `compromised_state` transitions according to rule table only.
4. **Isolation Effect Test**
   - Isolate compromised node.
   - Expected: lateral movement legal actions to/from isolated node are removed.
5. **Logging Completeness Test**
   - Run 5 timesteps.
   - Expected: each timestep log includes pre-state ref, outcomes, post-state diff, metric delta.

## Failure Modes
- Non-deterministic outcomes with same seed due to untracked randomness.
- Illegal action accepted because of incomplete state checks.
- Missing mandatory log fields per timestep.
- State mutation bypasses transition engine and breaks invariants.
- Scenario validator silently coerces malformed values.

## Acceptance Criteria
- All scenario inputs pass/fail deterministically with explicit validation behavior.
- Same seed + same action inputs produce equivalent trajectory hashes.
- Transition invariants hold (no impossible state transitions).
- Logging completeness ratio is 100% for required fields.
- Unit and integration manual tests above pass.

## Plan Revision Log
- 2026-03-28: Initial phase plan created.
