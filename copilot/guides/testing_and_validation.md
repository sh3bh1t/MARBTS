# Testing and Validation

## Authority
This file defines mandatory validation standards for all phases.

## Testing Philosophy
Every phase and major step must define:
- manual validation steps
- expected outcomes
- failure conditions
- acceptance criteria

No phase is complete without explicit validation evidence.

## Validation Targets (Mandatory)
For each implementation increment, validate:
1. State transitions
2. Agent decision quality and policy conformance
3. Logging completeness and schema correctness
4. Reproducibility under fixed seeds

## Validation Types
- Unit validation: schema checks, transition functions, policy primitives.
- Integration validation: environment-agent loop interactions.
- Simulation validation: end-to-end scenario behavior over timesteps.
- Reproducibility validation: repeated seeded runs produce equivalent outputs.
- Regression validation: previously passing deterministic scenarios remain stable.

## Manual Validation Template
For each step, provide:
- Goal: what is being validated
- Command(s): exact command line invocation
- Expected Output: concrete indicators in stdout/log artifacts
- Success Criteria: pass conditions
- Failure Conditions: specific signals requiring rollback or fix
- Artifacts: files/logs/plots generated as evidence

## Reproducibility Protocol
At minimum, every run record must include:
- run_id
- seed
- scenario_id
- config hash
- code commit hash
- simulation horizon
- timestamp

Validation procedure:
1. Run identical configuration at least twice with same seed.
2. Compare key outputs (action sequence hash, final compromise count, defense events).
3. Confirm equivalence within deterministic tolerance.

## Logging Completeness Criteria
Each timestep must log:
- pre-state snapshot reference
- red action intent and rationale
- blue action intent and rationale
- action outcomes
- post-state diff
- metric deltas

Any missing required field is a validation failure.

## Failure Escalation Rules
If validation fails:
1. Stop progression.
2. Isolate failing component and scope.
3. Document root cause hypothesis.
4. Patch design or implementation.
5. Re-run full relevant validation set.

## Definition of Done (Per Phase)
A phase is done only if:
- all acceptance criteria are met
- all mandatory validation targets pass
- reproducibility checks pass
- logs are complete and schema-valid
- known limitations are documented with mitigation plan
